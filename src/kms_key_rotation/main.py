import logging
import sys
import time
import base64
import json
import datetime

from os import getenv
from google.cloud import kms # pylint: disable=import-error
from google.api_core import exceptions # pylint: disable=import-error

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate a crypto key
    rotation period

    Args:

    data - Contains the Pub/Sub message
    context -  The Cloud Functions event metdata
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info("Received Cloud KMS crypto key creation or update log event. Evaluating rotation period.") # pylint: disable=line-too-long)

    # Determine if lockdown is running in view-only mode
    try:
        mode = getenv("MODE")
    except:
        logging.error("Mode not found in environment variable.")

    # Determine alerting Pub/Sub topic
    try:
        topic_id = getenv("TOPIC_ID")
    except:
        logging.error("Topic ID not found in environment variable.")

    # Determine alerting Pub/Sub topic
    try:
        alert_project = getenv('ALERT_GCP_PROJECT')
    except:
        logging.error('GCP alert project not found in environment variable.')


    # Converting log to json
    data_buffer = base64.b64decode(data["data"])
    log_entry = json.loads(data_buffer)

    # Parse log entry for variables
    crypto_key_id = log_entry["resource"]["labels"]["crypto_key_id"]
    project_id = log_entry["resource"]["labels"]["project_id"]
    key_ring_id = log_entry["resource"]["labels"]["key_ring_id"]
    location = log_entry["resource"]["labels"]["location"]

    # Check our project_id against allow / denylist
    if check_list(project_id):
        logging.info(
            f"The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.", # pylint: disable=line-too-long
        )
        # If the project ID is not in the allow / denylist
        # Continue with evaluation

        # Create the KMS client
        client = kms.KeyManagementServiceClient()

        # Build the parent key name.
        key_name = client.crypto_key_path(
            project_id,
            location,
            key_ring_id,
            crypto_key_id
        )

        # Call the function to capture
        # crypto key metadata
        crypto_key_metadata = get_key_data(client, key_name)

        # Get rotation period from key metadata
        rotation_period = find_rotation_period(crypto_key_metadata)

        # Review the rotation period against
        # approved rotation period. Defaults to 90d (7776000s)
        review_rotation_period(
            rotation_period,
            crypto_key_metadata,
            crypto_key_id,
            project_id,
            mode,
            topic_id
        )
    else:
        logging.info(
            f"The project {project_id} is in the allowlist or is not in the denylist. No action being taken." # pylint: disable=line-too-long
        )  

def get_key_data(client, key_name):
    """
    Gets KMS crypto key metadata.

    Args:
    client - The Cloud KMS client used to call APIs.
    key_name - The full crypto key resource name.

    Returns:
    crypto_key_metadata - Cloud KMS crypto key metadata
    """

    logging.info(f"Getting {key_name} metadata")
    try:
        crypto_key_metadata = client.get_crypto_key(name = key_name)
    except exceptions.PermissionDenied as perm_err:
        logging.error(f"Error getting crypto key {perm_err}")
        raise

    return crypto_key_metadata

def find_rotation_period(crypto_key_metadata):
    """
    Using the keys metadata, find the crypto keys rotation period

    Args:
    client - The Cloud KMS client used to call APIs.
    crypto_key_metadata - The crypto key"s metadata.

    Returns:
    rotation_period - The crypto key rotation period.
    """
    # Check to see if the crypto key is symmetric
    # Asymmetric encryption keys do not support rotation periods
    if crypto_key_metadata.primary.algorithm.GOOGLE_SYMMETRIC_ENCRYPTION == 1:
        logging.info(f"Cloud KMS crypto key {crypto_key_metadata.name} is a symmetric encryption key. Checking rotation period.")
    else:
        logging.info(f"Cloud KMS crypto key {crypto_key_metadata.name} is not using symmetric encryption, rotation periods are not supported. \n Exiting") # pylint: disable=line-too-long
        sys.exit(0)
    # If the crypto key does not have a rotation period
    # Set the period to 0
    if not crypto_key_metadata.rotation_period:
        logging.info(
            f"Cloud KMS crypto key {crypto_key_metadata.name} has no rotation period configured.",
        )

        # Set the rotation period to an unrealistic date
        # In 2021, this date would be year 2295
        rotation_period = 8639913600 # seconds
        return rotation_period
    # Return the rotation period for analysis
    else:
        # Capture the rotation period in days
        rotation_period_days = crypto_key_metadata.rotation_period.days
        logging.info(
            f"Cloud KMS crypto key {crypto_key_metadata.name} has a rotation period of {rotation_period_days} days.",
        )
        # Convert to seconds
        rotation_period = datetime.timedelta(seconds=24*60*60*rotation_period_days).total_seconds()

        return rotation_period

def review_rotation_period(rotation_period, crypto_key_metadata, crypto_key_id, project_id, mode, topic_id): # pylint: disable=line-too-long
    """
    Reviews the rotation period against a known value.
    If rotation period is over the value (aka longer) or None,
    call the remediate function to set to known value.

    Args:
    rotation_period - The crypto keys rotation period.
    crypto_key_metadata - The crypto keys metadata information.
    crypto_key_id - The crypto key ID for the pub/sub message.
    project_id - The project ID for the pub/sub message.
    mode - Lockdown mode for pub/sub message.
    topic_id - The pub/sub message topic ID.
    """

    # Determine alerting Pub/Sub topic
    try:
        alert_project = getenv('ALERT_GCP_PROJECT')
    except:
        logging.error('GCP alert project not found in environment variable.')

    # Get the approved rotation period for KMS keys
    try:
        approved_rotation_period = int(getenv("ROTATION_PERIOD"))
        logging.info(
            f"The Cloud KMS desired rotation period is {approved_rotation_period} days.",
        )
    except:
        logging.error("The KMS rotation period is not found in the environment variables.")

    # Convert approved rotation period to seconds
    approved_rotation_period_seconds = 60*60*24*approved_rotation_period

    # Configure Pub/Sub variables
    finding_type = "kms_bad_rotation_period"
    # Set our pub/sub message
    message = f"Unapproved rotation period on {crypto_key_id} in project: {project_id}."

    # Rotation period evaluation logic
    # If the rotation period on the crypto key is LONGER
    if rotation_period > approved_rotation_period_seconds:
        logging.info(
            f"Cloud KMS crypto key {crypto_key_metadata.name} has an invalid rotation period.",
        )
        logging.info(
            f"Cloud KMS crypto key rotation periods need to be {approved_rotation_period} days or less.",
        )

        # Publish message to Pub/Sub
        logging.info("Publishing alerting message to Pub/sub.")
        try:
            publish_message(
                finding_type,
                mode,
                crypto_key_metadata.name,
                alert_project,
                project_id,
                message,
                topic_id
            )
            logging.info(f"Published message to {topic_id}.")
        except:
            logging.error(f"Could not publish message to {topic_id}.")

        # Update the rotation period to specified value
        logging.info(f"Updating the rotation period on Cloud KMS crypto key {crypto_key_id}...", )
        update_rotation_period(crypto_key_metadata, crypto_key_id, approved_rotation_period_seconds)

    # Or if the rotation period is under
    elif rotation_period <= approved_rotation_period_seconds:
        logging.info(
            f"Cloud KMS crypto key {crypto_key_metadata.name} has a rotation period less than or equal to the requirement of {approved_rotation_period} days. Exiting.", # pylint: disable=line-too-long
        )

def update_rotation_period(crypto_key_metadata, crypto_key_id, approved_rotation_period_seconds):
    """
    Updates the crypto keys rotation period to known value.

    Args:
    crypto_key_metadata - The crypto keys metadata information.
    crypto_key_id - The Cloud KMS key ID.
    approved_rotation_period_seconds - The approved rotation period in seconds.
    """

    # Create the client.
    client = kms.KeyManagementServiceClient()

    # Set the key name for the update call
    crypto_key_name = crypto_key_metadata.name

    # Configure crypto key metadata
    key = {
        "name": crypto_key_name,
        "rotation_period": {
            "seconds": approved_rotation_period_seconds  # Rotate the key every X days.
        },
        "next_rotation_time": {
            "seconds": int(time.time()) + 60*60*24  # Start the first rotation in 24 hours.
        }
    }

    # Build the update mask to set a new retention policy.
    update_mask = {"paths": ["rotation_period", "next_rotation_time"]}

    # Update the rotation period
    try:
        logging.info(f"Attempting to update crypto key {crypto_key_id}")
        client.update_crypto_key(
            request={
            "crypto_key": key,
            "update_mask": update_mask
            }
        )
        logging.info(f"Update on {crypto_key_id} successful.")
    except exceptions.PermissionDenied as perm_err:
        logging.error(f"Error updating crypto key {perm_err}")

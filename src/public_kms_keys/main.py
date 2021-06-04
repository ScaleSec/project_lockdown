import base64
import json
import logging
import sys

from os import getenv
from google.cloud import kms # pylint: disable=import-error
from google.api_core import exceptions # pylint: disable=import-error


from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate Cloud KMS resources
    for public access and remediate if public access exists.

    Args:

    data - Contains the Pub/Sub message
    context -  The Cloud Functions event metdata
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received Cloud KMS permissions update log from Pub/Sub. Checking for public access..') # pylint: disable=line-too-long

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # If it isn't a crypto key update
    # and only key ring, we only need 3 below
    key_ring_id = log_entry['resource']['labels']['key_ring_id']
    location = log_entry['resource']['labels']['location']
    project_id = log_entry['resource']['labels']['project_id']

    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info("The project %s is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.", project_id) # pylint: disable=line-too-long
        # Create the Cloud KMS client
        client = kms.KeyManagementServiceClient()

        # If its a crpyto key perm update
        # versus a key ring update:
        if log_entry['resource']['type'] ==  "cloudkms_cryptokey":
            # create our crypto key var from the log file
            logging.info("Cloud KMS crypto key found in log.")
            crypto_key_id = log_entry['resource']['labels']['crypto_key_id']

            # Create our crypto key resource name using log variables
            kms_resource_name = client.crypto_key_path(
                project_id,
                location,
                key_ring_id,
                crypto_key_id)

        # If it is not a key perm update, we assume it is a key ring update
        # This assumption is based off of the log filter
        # which only catches 2 resources:
        # resource.type="cloudkms_cryptokey" OR resource.type="cloudkms_keyring"
        else:
            logging.info("Cloud KMS key ring found in log.")
            # Create our key ring resource name using log variables
            kms_resource_name = client.key_ring_path(project_id, location, key_ring_id)

        # Get our KMS resource IAM bindings (an IAM policy)
        kms_iam_policy = get_kms_iam_bindings(client, kms_resource_name)

        # Evaluate the IAM policy for public members:
        private_iam_policy = evaluate_iam_bindings(kms_iam_policy, kms_resource_name, project_id)

        # If public members were found
        # Send a pub/sub message for alerting
        # Update IAM policy if lockdown is in write mode
        if private_iam_policy:
            ###################
            ## Pub/Sub Logic ##
            ###################


            # Determine alerting Pub/Sub topic
            try:
                alert_project = getenv('ALERT_GCP_PROJECT')
            except:
                logging.error('GCP alert project not found in environment variable.')

            # Pub/sub topic ID is an env variable
            # Passed in via terraform deployment
            try:
                topic_id = getenv('TOPIC_ID')
            except:
                logging.error('Topic ID not found in environment variable.')
            # Finding type is used in pub/sub message
            finding_type = "public_kms_resource"
            # Set our pub/sub message
            message = f"Found public members on: {kms_resource_name} in project: {project_id}."
            # Publish message to Pub/Sub
            logging.info("Publishing message to Pub/Sub.")
            try:
                publish_message(
                    finding_type,
                    mode,
                    kms_resource_name,
                    alert_project,
                    project_id,
                    message,
                    topic_id)
                logging.info("Published message to %s", topic_id)
            except:
                logging.error("Could not publish message to %s", topic_id)
                raise

            #######################
            ## Remediation Logic ##
            #######################
            # if the function is running in "write" mode, remove public members
            if mode == "write":
                logging.info("Lockdown is in write mode. Removing public IAM members.")
                # Removes the public IAM bindings from the KMS resource for this specific role
                remove_public_iam_members_from_policy(
                    client,
                    kms_resource_name,
                    private_iam_policy,
                    project_id)
            # if function is in read mode, take no action
            if mode == "read":
                logging.info("Lockdown is in read-only mode. Taking no action.")
    else:
        logging.info("The project %s is in the allowlist or is not in the denylist. No action being taken.", project_id) # pylint: disable=line-too-long

def get_kms_iam_bindings(client, kms_resource_name):
    """
    Retrieve the IAM bindings on the Cloud KMS key ring

    Args:
    client - Cloud KMS client. Used to call methods.
    kms_resource_name - The Cloud KMS resource name.

    Returns:

    kms_iam_policy - The IAM policy (collection of bindings)
    """

    logging.info("Getting IAM policy on Cloud KMS resource: %s", kms_resource_name)

    # Get the IAM policy for the Cloud KMS resource
    try:
        kms_iam_policy = client.get_iam_policy(request={"resource": kms_resource_name})
    except exceptions.PermissionDenied as perm_err:
        logging.error(perm_err)
        sys.exit(1)

    return kms_iam_policy

def evaluate_iam_bindings(kms_iam_policy, kms_resource_name, project_id):
    """
    Checks IAM policies bindings for public
    members "allUsers" and "allAuthenticatedUsers"

    Args:

    kms_iam_policy - The IAM policy attached to the resource.
    kms_resource_name - The Cloud KMS resource name.
    project_id - The GCP project where the KMS resource lives.

    Returns:

    kms_iam_policy - The private IAM policy for Cloud KMS resource.
    """

    logging.info("Evaluating IAM bindings on Cloud KMS resource: %s", kms_resource_name)
    # Create the public users list to reference when creating new members.
    public_users = ["allAuthenticatedUsers", "allUsers"]

    # Evaluate each binding in the IAM policy
    for binding in kms_iam_policy.bindings:
        members = binding.members
        # Iterate in reverse because we remove strings
        # if they are public
        for member in reversed(members):
            if member in public_users:
                logging.info("Found a public member on Cloud KMS resource: %s in project: %s", kms_resource_name, project_id) # pylint: disable=line-too-long
                # Remove the public member from the IAM binding
                binding.members.remove(member)
                # This local variable is used to return the new policy
                # if public member(s) are found
                public = "true"

    # If we set a local variable of "public"
    # return the new KMS IAM policy
    if "public" in locals():
        return kms_iam_policy
    else:
        logging.info("The IAM policy on the Cloud KMS resource: %s is private.", kms_resource_name)
        sys.exit(0)

def remove_public_iam_members_from_policy(client, kms_resource_name, private_iam_policy, project_id): # pylint: disable=line-too-long
    """
    Takes a dictionary of roles with public members
    and removes them from the Cloud KMS resource.

    Args:

    client - Cloud KMS client. Used to call methods.
    kms_resource_name - The Cloud KMS resource name.
    private_iam_policy - The private IAM policy for Cloud KMS resource.
    project_id - The GCP project where the Cloud KMS resource lives
    """

    logging.info("Updating IAM policy on Cloud KMS resource: %s", kms_resource_name)

    # Create the request body to update the IAM policy
    request = {
        'resource': kms_resource_name,
        'policy': private_iam_policy
    }

    # Set the new KMS resource policy
    try:
        client.set_iam_policy(request=request)
        logging.info("Finished updating the IAM permissions on KMS resource: %s in project: %s", kms_resource_name, project_id) # pylint: disable=line-too-long
    except:
        logging.error("Could not update the IAM permissions on KMS resource: %s in project %s", kms_resource_name, project_id) # pylint: disable=line-too-long
        raise

import base64
import json
import logging

from os import getenv
from googleapiclient import discovery

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate
    the IAM bindings attached to service accounts.

    Args:
        data: Contains the Pub/Sub message
        context:  The Cloud Functions event metdata
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info(
        "Received a service account IAM policy update from Pub/Sub. Checking for risky roles."
    )

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Determine alerting Pub/Sub topic
    try:
        topic_id = getenv('TOPIC_ID')
    except:
        logging.error('Topic ID not found in environment variable.')

    try:
        risky_roles = getenv('RISKY_ROLES')
    except:
        logging.error('Risky roles not found in environment variable.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Get the service account name from the log event
    sa_resource_name = log_entry["protoPayload"]["request"]["resource"]
    # Get the project ID to check against allow/denylist
    project_id = log_entry['resource']['labels']['project_id']

    # Create our IAM client
    iam_client = create_client()

    # Get the IAM policy attached to the service account
    sa_iam_policy = get_sa_iam_policy(iam_client, sa_resource_name)

    # Analyze the returned IAM policy for risky roles
    risky_role_asssigned = analyze_policy(sa_iam_policy, sa_resource_name, risky_roles)

    # If a risky role was found
    if risky_role_asssigned:
        # Check our project_id against the project list set at deployment
        if check_list(project_id):
            logging.info(f"The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.")

            # Create the pub/sub alerting variables
            finding_type = "protect_lockdown_sa"
            # Set our pub/sub message
            message = f"Found a risky role on the service account: {sa_resource_name}."
            # Publish message to Pub/Sub
            logging.info('Publishing message to Pub/Sub.')
            try:
                publish_message(
                    finding_type,
                    mode,
                    sa_resource_name,
                    project_id,
                    message,
                    topic_id
                )
                logging.info(
                    f"Published message to {topic_id}"
                )
            except:
                logging.error(
                    f"Could not publish message to {topic_id}"
                )
                raise
            # if the function is running in "write" mode, remove risky roles
            if mode == "write":
                logging.info(
                    "Lockdown is in write mode. Removing risky roles from service account."
                )
                # Generate new IAM policy
                new_policy = remediate_iam_policy(sa_iam_policy, sa_resource_name, risky_roles)
                # Update SA IAM policy with new IAM policy
                update_new_policy(new_policy, iam_client, sa_resource_name)
            # if function is in read mode
            if mode == "read":
                logging.info("Lockdown is in read-only mode. Taking no action.")
    else:
        logging.info(
            f"No risky roles found. Taking no action on service account: {sa_resource_name}"
        )


def get_sa_iam_policy(iam_client, sa_resource_name):
    """Gets the IAM policy for the service account.

    Args:
        iam_client [class object]: The GCP IAM client.
        sa_resource_name ([str]): The GCP service account full resource name.

    Returns:
        [dict]: The IAM policy attached to the sa_resource_name.
    """

    try:
        logging.info(
            f"Getting IAM policy for service account {sa_resource_name}"
        )
        request = iam_client.projects().serviceAccounts().getIamPolicy(
            resource=sa_resource_name
        )
        sa_iam_policy = request.execute()
    except Exception as e:
        logging.error(
            f"Error retrieving IAM policy. Error message: {e}"
        )

    logging.info(
        "IAM policy retrieval successful"
    )

    return sa_iam_policy


def analyze_policy(sa_iam_policy, sa_resource_name, risky_roles):
    """Check for the existence of risky roles.

    Args:
        sa_iam_policy ([dict]): The IAM policy attached to the sa_resource_name.
        sa_resource_name ([str]): The GCP service account full resource name.
        risky_roles ([list]): A list of risky roles to check current attached roles against.

    Returns:
        [bool]: True is a risky role was found in the IAM policy.
    """

    for binding in sa_iam_policy["bindings"]:
        if binding["role"] in risky_roles:
            logging.info(
                f"Found IAM role from denied list on service account {sa_resource_name}"
            )

            return True


def remediate_iam_policy(sa_iam_policy, sa_resource_name, risky_roles):
    """Remove risky IAM roles from the service account IAM policy.

    Args:
        sa_iam_policy ([dict]): The IAM policy attached to the sa_resource_name.
        sa_resource_name ([str]): The GCP service account full resource name.
        risky_roles ([list]): A list of risky roles to check current attached roles against.

    Returns:
        [dict]: An updated non-risky IAM policy. All risky roles removed.
    """

    # We iterate in reverse due to removing entries
    for binding in reversed(sa_iam_policy["bindings"]):
        if binding["role"] in risky_roles:
            role = binding["role"]
            logging.info(
                f"Removing risky role: {role} from {sa_resource_name}"
            )
            sa_iam_policy["bindings"].remove(binding)
        else:
            logging.info(f"IAM binding: {binding} does not contain risky role.")

    return sa_iam_policy


def update_new_policy(new_policy, iam_client, sa_resource_name):
    """Updates target SA with new IAM policy.

    Args:
        new_policy ([dict]): An updated non-risky IAM policy. All risky roles removed.
        iam_client [class object]: The GCP IAM client.
        sa_resource_name ([str]): The GCP service account full resource name.
    """

    body = {
        "policy": new_policy
    }
    try:
        logging.info(
            f"Updating IAM policy on service account {sa_resource_name}"
        )
        request = iam_client.projects().serviceAccounts().setIamPolicy(
            resource=sa_resource_name,
            body=body
        )
        request.execute()
        logging.info(
            "IAM policy update successful"
        )
    except Exception as e:
        logging.error(
            f"An error {e} has occured when attempting to update the IAM policy on service account {sa_resource_name}"
        )


def create_client():
    """Creates a GCP IAM client.

    Returns:
        [class object]: The GCP IAM client.
    """

    try:
        logging.info("Creating IAM client..")
        iam_client = discovery.build('iam', 'v1')
    except:
        logging.error("Could not create IAM client.")

    return iam_client

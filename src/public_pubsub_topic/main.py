import base64
import json
import logging

from os import getenv
from google.cloud import pubsub_v1

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the Pub/Sub topic permissions for public members.
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received Pub/Sub topic update log from Pub/Sub. Checking for public members.')

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

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Parse project id and resource name for allow/deny list checking and remediation
    resource_name = log_entry['protoPayload']['resourceName'].split('/')
    project_id = resource_name[1]
    topic_to_evaluate = resource_name[-1]


    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info(f'The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.')

        # Create PubSub Client
        client = pubsub_v1.PublisherClient()
        topic_path = client.topic_path(project_id, topic_to_evaluate)

        # Get a copy of the current policy
        try:
            policy = client.get_iam_policy(request={"resource": topic_path})
        except:
            logging.error(f'Could not retrieve current policy from {topic_to_evaluate}')

        # Evaluate policy and return clean policy without public bindings
        all_users_found, new_policy = eval_iam_policy(client, policy)

        # If a public binding was found, we need to remediate. 
        if all_users_found:
            finding_type = "public_topic_policy"
            # Set our pub/sub message
            message = f"Found public members on PubSub Topic: {topic_to_evaluate} in project: {project_id}."
            # Publish message to Pub/Sub
            logging.info(f'Publishing message to Pub/Sub.')
            try:
                publish_message(finding_type, mode, topic_to_evaluate, project_id, message, topic_id)
                logging.info(f'Published message to {topic_id}')
            except:
                logging.error(f'Could not publish message to {topic_id}')
                raise
            if mode == "write":
                logging.info(f"Lockdown is in write mode. Updating topic policy: {topic_to_evaluate} with new IAM policy.")
                # Updates topic with private IAM policy
                set_iam_policy(new_policy, client, topic_path, project_id)
            if mode == "read":
                logging.info('Lockdown is in read-only mode. Taking no action.')
        else:
            logging.info(f"Did not find public members on PubSub Topic: {topic_to_evaluate} in project: {project_id}.")

    else:
        logging.info(f'The project {project_id} is in the allowlist or is not in the denylist. No action being taken.')

def eval_iam_policy(client, policy):
    """
    Check for public IAM members in topic policy.

    Returns:
        bool was_public if allUsers or allAuthenticatedUsers was found
        IAM Policy new_policy
    """

    # Set bool to false, will be true if allusers are found
    was_public = False 

    # There may not be any bindings to check, so verify that first
    if policy.bindings:
        for binding in policy.bindings:
            # Check if allUsers or allAuthenticatedUsers is in any of the bindings and remove it if found.
            if 'allUsers' in binding.members:
                binding.members.remove('allUsers')
                was_public = True
            if 'allAuthenticatedUsers' in binding.members:
                binding.members.remove('allAuthenticatedUsers')
                was_public = True

    return was_public, policy

def set_iam_policy(policy, client, topic_path, project_id):
    """
    Sets a topic policy to a new version
    """
    try:
        policy = client.set_iam_policy(request={"resource": topic_path, "policy": policy})
    except:
        logging.error(f'Could not set topic {topic_path} policy.')
        raise

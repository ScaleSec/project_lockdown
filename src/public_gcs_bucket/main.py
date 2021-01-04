import base64
import json
import logging

from os import getenv
from google.cloud import storage

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate bucket for public access and remediate if public access exists.
    """

    # Integrates cloud logging handler to python logging
    create_logger()

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    logging.info('Received GCS permissions update log from Pub/Sub. Checking for public access.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Setting GCS bucket name and project ID variables from log
    bucket_name = log_entry['resource']['labels']['bucket_name']
    project_id = log_entry['resource']['labels']['project_id']

    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info(f'The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.')
        # Configuring storage client
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)

        # Get the current GCS bucket policy
        try:
            policy = bucket.get_iam_policy()
        except:
            logging.error(f'Could not view bucket: {bucket_name} IAM policy.')

        # Evaluating GCS bucket policy for public bindings
        eval_bucket(bucket_name, policy, bucket, project_id, mode)
    else:
        logging.info(f'The project {project_id} is in the allowlist or is not in the denylist. No action being taken.')

def eval_bucket(bucket_name, policy, bucket, project_id, mode):
    """
    Evaluates a bucket for public access and returns list of public members and roles.
    """

    try:
        topic_id = getenv('TOPIC_ID')
    except:
        logging.error('Topic ID not found in environment variable.')

    for role in policy:
        # Empty list to add public IAM bindings to
        member_bindings_to_remove = {}
        # For each IAM binding, find the members
        members = policy[role]
        # For every member, check if they are public
        for member in members:
            if member == "allAuthenticatedUsers" or member == "allUsers":
                # Add member and role to list if member is public
                member_bindings_to_remove[member] = role
                logging.info(f'Found public member: {member} with role: {role} on bucket: {bucket_name} in project: {project_id}.')
            else:
                logging.info(f'Member {member} with role {role} is not public.')
        if member_bindings_to_remove:
            # If we have public members, we set this variable to trigger our Pub/Sub message publish
            public = "true"
            logging.info(f'List of public IAM bindings to remove for role: {role} - {member_bindings_to_remove}.')
            # if the function is running in "write" mode, remove public members
            if mode == "write":
                logging.info('Lockdown is in write mode. Removing public IAM members.')
                # Removes the public IAM bindings from the bucket for this specific role
                remove_public_iam_members_from_policy(bucket_name, member_bindings_to_remove, bucket)
            # if function is in read mode, take no action and publish message to pub/sub
            if mode == "read":
                logging.info('Lockdown is in read-only mode. Taking no action.')
        else:
            logging.info(f'No public members found on bucket {bucket_name} with role: {role}.')

    if "public" in locals():
        finding_type = "public_gcs_bucket"
        # Set our pub/sub message
        message = f"Found public members on bucket: {bucket_name} in project: {project_id}."
        # Publish message to Pub/Sub
        logging.info('Publishing message to Pub/Sub.')
        try:
            publish_message(finding_type, mode, bucket_name, project_id, message, topic_id)
            logging.info(f'Published message to {topic_id}')
        except:
            logging.error(f'Could not publish message to {topic_id}')
            raise
        
def remove_public_iam_members_from_policy(bucket_name, member_bindings_to_remove, bucket):
    """
    Takes a dictionary of roles with public members and removes them from a GCS bucket Policy object.
    """
    # Re-checks the bucket policy to catch previously made updates
    # This is critical in the event that a user makes a `setIamPermissions` API call
    # with 1> member and >=2 roles due to the way we iterate over roles
    try:
        policy = bucket.get_iam_policy()
    except:
        logging.error('Could not view bucket: {} IAM policy.'.format(bucket_name))

    # Remove public members from GCS bucket policy
    for member in member_bindings_to_remove:
        policy[member_bindings_to_remove[member]].discard(member)

    # Set the new bucket policy
    try:
        bucket.set_iam_policy(policy)
        logging.info('Finished updating the IAM permissions on bucket: {} for role: {}'.format(bucket_name, member_bindings_to_remove[member]))
    except:
        logging.error('Could not update the IAM permissions on bucket: {}.'.format(bucket_name))
        raise
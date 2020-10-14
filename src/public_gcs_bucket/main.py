import datetime
import pytz
import base64
import json
import logging

from google.cloud import storage
from google.cloud import logging as glogging

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate bucket for public access and remediate if public access exists.
    """

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info('Received GCS permissions update log from Pub/Sub. Checking for public access.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Setting GCS bucket name and project ID variables from log
    bucket_name = log_entry['resource']['labels']['bucket_name']
    project_id = log_entry['resource']['labels']['project_id']

    # Configuring storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # Get the current GCS bucket policy
    try:
        policy = bucket.get_iam_policy()
    except:
        logging.error('Could not view bucket: {} IAM policy.'.format(bucket_name))

    # Evaluating GCS bucket policy for public bindings
    eval_bucket(project_id, bucket_name, policy, bucket)

def eval_bucket(project_id, bucket_name, policy, bucket):
    """
    Evaluates a bucket for public access and returns list of public members and roles.
    """

    for role in policy:
        # Empty list to add public IAM bindings to
        member_bindings_to_remove = {}

        # For each IAM binding, find the role and member
        members = policy[role]

        # For every member, check if they are public
        for member in members:
            if member == "allAuthenticatedUsers" or member == "allUsers":
                # Add member to list if member is public
                member_bindings_to_remove[member] = role
                logging.info('Found public member: {} with role: {} on bucket: {}.'.format(member, role, bucket_name))
            else:
                logging.info('Member {} with role {} is not public.'.format(member, role))

        if member_bindings_to_remove:
            logging.info('List of public IAM bindings to remove for role: {} - {}'.format(role, member_bindings_to_remove))
            # Removes the public IAM bindings from the bucket for this specific role and returns the new bucket policy
            remove_public_iam_members_from_policy(bucket_name, member_bindings_to_remove, bucket)

def remove_public_iam_members_from_policy(bucket_name, member_bindings_to_remove, bucket):
    """
    Takes a dictionary of roles with public members and removes them from a GCS bucket Policy object.  
    Returns the bucket Policy without public members.
    """
    # Re-checks the bucket policy to catch previously made updates
    # This is critical in the event that a user makes a `setIamPermissions` API call
    # with 1> member and >=2 roles due to the way we iterate over roles
    policy = bucket.get_iam_policy()

    # Remove public members from GCS bucket policy
    for member in member_bindings_to_remove:
        policy[member_bindings_to_remove[member]].discard(member)

    # Set the new private bucket policy
    try:
        bucket.set_iam_policy(policy)
        logging.info('Finished updating the IAM permissions on bucket: {} for role: {}'.format(bucket_name, member_bindings_to_remove[member]))
    except:
        logging.error('Could not update the IAM permissions on bucket: {}.'.format(bucket_name))
        raise

def create_logger():

    # Instantiates a cloud logging client
    client = glogging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module
    client.get_default_handler()
    client.setup_logging()

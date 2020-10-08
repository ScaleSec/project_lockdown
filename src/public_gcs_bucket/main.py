import datetime
import pytz
import base64
import json
import logging

from google.cloud import storage
import google.cloud.logging

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate bucket for public access and remediate if public access exists
    """

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info("Received GCS public remediation log from Pub/Sub.")

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Setting GCS bucket name and project ID variables from log
    bucket_name = log_entry['resource']['labels']['bucket_name']
    project_id = log_entry['resource']['labels']['project_id']
    
    # Configuring storage client
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    policy  = bucket.get_iam_policy()

    # Evaluating GCS bucket policy for public bindings
    role_bindings_to_remove = eval_bucket(project_id, bucket_name, policy)
    
    if role_bindings_to_remove:
        # Removes the public IAM bindings from the bucket and returns the new bucket policy
        remediated_policy = remove_public_iam_members_from_policy(bucket_name, role_bindings_to_remove)

        # Sets the new bucket policy
        bucket.set_iam_policy(remediated_policy)

        logging.info('Finished updating {} IAM Policy'.format(bucket_name))
    else:
        logging.info('No Members to remove from {}'.format(bucket_name))

def eval_bucket(project_id, bucket_name, policy):
    """
    Evaluates a bucket for public access and returns list of public members and roles
    """
    # Empty list to add public IAM bindings to
    role_bindings_to_remove = {}

    for role in policy:
        # For each IAM binding, find the role and member
        members = policy[role]
        text = 'Role: {}, Members: {}'.format(role, members)
        logging.info(text)

        # For every member, check if they are public
        for x in members:
            if x == "allAuthenticatedUsers" or x == "allUsers":
                # Add role to list if member is public
                role_bindings_to_remove.update({role : x})
                logging.info('Found {} with role {} on {}.'.format(x, role, bucket_name))
            else:
                logging.info("Member {} with role {} is not public.".format(x, role))

    logging.info("Total list of public IAM bindings to remove: {}".format(role_bindings_to_remove))

    return role_bindings_to_remove

def remove_public_iam_members_from_policy(bucket_name, role_bindings_to_remove):
    """
    Takes a dictionary of roles with public members and removes them from an IAM Policy.  Returns IAM Policy without public memebers.
    """

    # Create storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    policy = bucket.get_iam_policy()

    # Remove public members from GCS bucket policy
    for role in role_bindings_to_remove:
        policy[role].discard(role_bindings_to_remove[role])
        logging.info('Removed member {} with role {} from {}.'.format(role_bindings_to_remove[role], role, bucket_name))

    # Return updated private bucket policy
    return policy


def create_logger():
    
    # Instantiates a cloud logging client
    client = google.cloud.logging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module
    client.get_default_handler()
    client.setup_logging()
import logging
import datetime
import pytz
from google.cloud import storage
import base64
import json

logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate bucket for public access and remediate if public access exists
    """
    logging.info("Received log containing the storage.setIamPermissions using Pub/Sub")

    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    bucket_name = log_entry['resource']['labels']['bucket_name']
    project_id = log_entry['resource']['labels']['project_id']

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    policy  = bucket.get_iam_policy()
    members_to_remove = eval_bucket(project_id,bucket_name, policy)
    
    if bool(members_to_remove) != False:
        remediated_policy = remove_public_iam_members_from_policy(bucket_name,members_to_remove)
        bucket.set_iam_policy(remediated_policy)
        logging.info('Finished updating {} IAM Policy'.format(bucket_name))
    else:
        logging.info('No Members to remove from {}'.format(bucket_name))

def eval_bucket(project_id, bucket_name, policy):
    """
    Evaluates a bucket for public access and returns list of public members and roles
    """
    members_to_remove = {}
    for role in policy:
        members = policy[role]
        print('Role: {}, Members: {}'.format(role, members))
        for x in members:
            if  x == "allAuthenticatedUsers" or x == "allUsers":
                members_to_remove.update({role : x})
                logging.info('Removed {} with role {} from {}.'.format(x, role, bucket_name))
            else:
                logging.info("Member {} in role {} not a public members in {}".format(x, role,bucket_name))

    logging.info("Members to remove {}".format(members_to_remove))

    return members_to_remove

def remove_public_iam_members_from_policy(bucket_name, members_to_remove):
    """
    Takes a dictionary of roles and members to remove and removes them from an IAM Policy.  Returns IAM Policy without public memebers
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    policy = bucket.get_iam_policy()
    for role in members_to_remove:
        policy[role].discard(members_to_remove[role])
        logging.info('Removed member {} with role {} from {}.'.format(members_to_remove[role], role, bucket_name))

    return policy
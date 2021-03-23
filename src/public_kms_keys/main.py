import base64
import json
import logging
import sys

from os import getenv
from google.cloud import kms
from google.api_core import exceptions


from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate Cloud KMS resources 
    for public access and remediate if public access exists.

    Arguments:

    data - Contains the Pub/Sub message 
    context -  The Cloud Functions event metdata
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received Cloud KMS permissions update log from Pub/Sub. Checking for public access..')

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # If it isn't a key and only key ring, we only need 3 below
    key_ring_id = log_entry['resource']['labels']['key_ring_id']
    location = log_entry['resource']['labels']['location']
    project_id = log_entry['resource']['labels']['project_id']

    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info(f'The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.')
        # Create the Cloud KMS client
        client = kms.KeyManagementServiceClient()

        # If its a key perm update versus a key ring update:
        if log_entry['resource']['type'] ==  "cloudkms_cryptokey":
            # create our crypto key var from the log file
            logging.info("Cloud KMS crypto key found in log.")
            crypto_key_id = log_entry['resource']['labels']['crypto_key_id']

            # Create our crypto key resource name using log variables
            kms_resource_name = client.crypto_key_path(project_id, location, key_ring_id, crypto_key_id)

        # If it is not a key perm update, we assume it is a key ring update
        # This assumption is based off of the log filter 
        # which only catches 2 resources:
        # resource.type="cloudkms_cryptokey" OR resource.type="cloudkms_keyring"
        else:
            logging.info("Cloud KMS key ring found in log.")
            # Create our key ring resource name using log variables
            kms_resource_name = client.key_ring_path(project_id, location, key_ring_id)
            
        # Get our KMS resource IAM bindings (an IAM policy)
        kms_iam_binding = get_kms_iam_bindings(client, kms_resource_name)
        
        # Evaluate the IAM policy for public members:
        member_bindings_to_remove = evaluate_iam_bindings(kms_iam_binding)

        # If public members were found
        # Send a pub/sub message for alerting
        # Update IAM policy if lockdown is in write mode
        if member_bindings_to_remove:
            ###################
            ## Pub/Sub Logic ##
            ###################

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
                publish_message(finding_type, mode, kms_resource_name, project_id, message, topic_id)
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
                remove_public_iam_members_from_policy(client, kms_resource_name, member_bindings_to_remove)
            # if function is in read mode, take no action
            if mode == "read":
                logging.info("Lockdown is in read-only mode. Taking no action.")

    else:
        logging.info("The project %s is in the allowlist or is not in the denylist. No action being taken.", project_id)

def get_kms_iam_bindings(client, kms_resource_name):
    """
    Retrieve the IAM bindings on the Cloud KMS key ring

    Arguments:
    client - Cloud KMS client. Used to call methods.
    kms_resource_name - The Cloud KMS key ring resource name

    Returns:

    kms_iam_policy - The IAM policy (collection of bindings)
    """

    # Get the IAM policy for the crypto key ring
    try:
        kms_iam_policy = client.get_iam_policy(request={"resource": kms_resource_name})
    except exceptions.PermissionDenied as perm_err:
        logging.error(perm_err)
        sys.exit(1)
    print(kms_iam_policy)

    return kms_iam_policy

def evaluate_iam_bindings(kms_iam_policy):
    """
    Checks IAM policies bindings for public 
    members "allUsers" and "allAuthenticatedUsers"

    Arguments:

    kms_iam_policy - The IAM policy attached to the resource.

    Returns:

    member_bindings_to_remove - The public IAM bindings from the Cloud KMS resource.
    """

    for role in kms_iam_policy:
        # Empty list to add public IAM bindings to
        member_bindings_to_remove = {}
        # For each IAM binding, find the members
        members = kms_iam_policy[role]
        # For every member, check if they are public
        for member in members:
            if member == "allAuthenticatedUsers" or member == "allUsers":
                # Add member and role to list if member is public
                member_bindings_to_remove[member] = role
                logging.info(f"Found public member: {member} with role: {role}.")
            else:
                logging.info(f"Member {member} with role {role} is not public.")
    # If public members were found, return new private IAM bindings list
    if member_bindings_to_remove:
        logging.info("Found public members: %s", member_bindings_to_remove)
        return member_bindings_to_remove
    else:
        logging.info("No public members found.")
        sys.exit(0)

def remove_public_iam_members_from_policy(client, kms_resource_name, member_bindings_to_remove):
    """
    Takes a dictionary of roles with public members 
    and removes them from the Cloud KMS resource.

    Arguments:

    client - Cloud KMS client. Used to call methods. 
    kms_resource_name - The Cloud KMS resource name
    member_bindings_to_remove - List of public IAM bindings to remove.
    """

    # Re-checks the KMS resource policy to catch previously made updates
    # This is critical in the event that a user makes a `setIamPolicy` API call
    # with 1> member and >=2 roles due to the way we iterate over roles

    try:
        kms_iam_policy = get_kms_iam_bindings(client, kms_resource_name)
    except exceptions.PermissionDenied as perm_err:
        logging.error(perm_err)
        sys.exit(1)

    # Remove public members from KMS resource policy
    for member in member_bindings_to_remove:
        kms_iam_policy[member_bindings_to_remove[member]].discard(member)

    # Set the new KMS resource policy
    try:
        client.set_iam_policy(kms_resource_name, kms_iam_policy)
        logging.info("Finished updating the IAM permissions on KMS resource: %s for role: %s", kms_resource_name, member_bindings_to_remove[member])
    except:
        logging.error("Could not update the IAM permissions on KMS resource: %s", kms_resource_name)
        raise

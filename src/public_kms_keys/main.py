import base64
import json
import logging

from os import getenv
from google.cloud import kms

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate Cloud KMS resources 
    for public access and remediate if public access exists.

    Arguments:

    data - ##TODO
    context -  ##TODO
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received Cloud KMS permissions update log from Pub/Sub. Checking for public access..')

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Create the Cloud KMS client
    client = kms.KeyManagementServiceClient()

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)
    
    
    # If it isn't a key and only key ring, we only need 3 below
    keyring_id = log_entry['resource']['labels']['key_ring_id']
    location = log_entry['resource']['labels']['location']
    project_id = log_entry['resource']['labels']['project_id']

    # If its a key perm update, we need crypto_key_id var and the 3 above
    # to create our resource name
    if log_entry['resource']['type'] ==  "cloudkms_cryptokey":
        cryptokey_id = log_entry['resource']['labels']['crypto_key_id']

    # Create our key ring resource name using log variables
    keyring_resource_name = f"projects/{project_id}/locations/{location}/keyRings/{keyring_id}"

    # Create our crypto key resource name using log variables
    cryptokey_resource_name = f"projects/{project_id}/locations/{location}/keyRings/{keyring_id}/cryptoKeys/{cryptokey_id}"



def get_keyring_iam_bindings(client, keyring_resource_name):
    """
    Retrieve the IAM bindings on the Cloud KMS key ring

    Arguments:

    keyring_resource_name - The Cloud KMS key ring resource name
    """

    keyring_iam_policy = client.get_iam_policy(resource = keyring_resource_name)

    return keyring_iam_policy

def get_cryptokey_iam_bindings(client, cryptokey_resource_name):
    """
    Retrieve the IAM bindings on the Cloud KMS crypto key

    Arguments:

    cryptokey_resource_name - The Cloud KMS crypto key resource name
    """

    cryptokey_iam_policy = client.get_iam_policy(resource = cryptokey_resource_name)

    return cryptokey_iam_policy
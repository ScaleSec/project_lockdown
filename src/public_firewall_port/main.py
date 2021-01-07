from base64 import b64decode
import json
import logging
import gc

from os import getenv
from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from googleapiclient.discovery_cache.base import Cache
import googleapiclient.discovery


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate firewall rules with 0.0.0.0/0 source ingress.
    """

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

    # Create compute client to make API calls
    compute_client = create_service()

    # Integrates cloud logging handler to python logging
    create_logger()

    # Converting log to json
    data_buffer = b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Get firewall_name from log event and remove project identifiers
    resource_name = log_entry['protoPayload']['resourceName'].split('/')
    logging.info(f'Received firewall create/update log from Pub/Sub. Checking firewall: {resource_name} for enablement status.')
    del log_entry
    firewall_name = resource_name[-1]
    project_id = resource_name[1]

    # Get firewall information
    firewall_metadata = describe_firewall(compute_client, firewall_name, project_id)

    # Extract info about the firewall to check if it has 0.0.0.0/0 and if it is enabled.
    source_ranges = firewall_metadata['sourceRanges']
    disabled = firewall_metadata['disabled']

    if ('0.0.0.0/0' in source_ranges and not disabled):
        finding_type = "public_firewall_port"
        # Set our pub/sub message
        message = f"Found 0.0.0.0/0 ingress on enabled firewall rule: {firewall_name} in project: {project_id}."
        # Publish message to Pub/Sub
        logging.info(f'Publishing message to Pub/Sub.')
        try:
            logging.info(message)
            publish_message(finding_type, mode, firewall_name, project_id, message, topic_id)
            logging.info(f'Published message to {topic_id}')
        except:
            logging.error(f'Could not publish message to {topic_id}')
            raise
        if mode == "write":
            logging.info(f"Lockdown is in write mode. Disabling firewall rule: {firewall_name}.")
            # Disables the firewall rule
            disable_firewall(compute_client, firewall_name, project_id)
        if mode == "read":
            logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f"The firewall rule: {firewall_name} is not enabled or 0.0.0.0/0 was removed.")

    # This function sits around 133mb of memory usage at creation date, if we don't cleanup, high activity projects may run into issues.
    del compute_client
    gc.collect()

def describe_firewall(compute_client, firewall_name, project_id):
    """ Gets information about the firewall
    """
    try:
        request = compute_client.firewalls().get(project=project_id, firewall=firewall_name)
        response = request.execute(num_retries=5)
    except:
        logging.info(f'Could not retrieve enablement status for {firewall_name}.')
        raise
    return response

def disable_firewall(compute_client, firewall_name, project_id):
    """ Disables a firewall rule
    """
    firewall_body = {
    "name": firewall_name,
    "disabled": "true"
    }
    try:
        request = compute_client.firewalls().patch(project=project_id, firewall=firewall_name, body=firewall_body)
        response = request.execute(num_retries=5)
    except:
        logging.info(f'Could not disable firewall: {firewall_name}.')
        raise

def create_service():
    """
    Creates the GCP Compute Service.
    """
    return googleapiclient.discovery.build('compute', 'v1', cache=MemoryCache())

class MemoryCache(Cache):
    """
    File-based cache to resolve GCP Cloud Function noisey log entries.
    """
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content

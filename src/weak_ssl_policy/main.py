import base64
import json
import logging

from os import getenv
from google.cloud import logging as glogging
from google.cloud import pubsub_v1
from googleapiclient.discovery_cache.base import Cache
import googleapiclient.discovery

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the SSL policy for a weak TLS.
    """


    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Create compute client to make API calls
    compute_client = create_service()

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info('Received SSL policy log from Pub/Sub. Checking for weak TLS.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    ssl_policy = log_entry['protoPayload']['resourceName']

    # Create the ssl policy resource ID
    # Split the ssl_policy into a list of strings
    ssl_list = ssl_policy.split('/')
    # Set our list of strings to remove
    remove_strings = ["projects", "global", "sslPolicies"]
    # Remove all strings in list to create a list project_id and ssl_policy
    ssl_project_id = [i for i in ssl_list if i not in remove_strings]
    # Create the project_id and ssl_policy variables
    project_id = ssl_project_id[0]
    ssl_policy = ssl_project_id[1]

    # Capture the SSL Policy's metadata
    ssl_description = get_ssl_policy(project_id, ssl_policy, compute_client)

    # Only return the tls_version variable if it is TLS 1.0 (weak)
    tls_version = analyze_ssl_policy(ssl_description, project_id, compute_client, ssl_policy)

    # if the variable tls_version exists, update to TLS 1.1
    if tls_version:
        # Set our pub/sub message
        message = f"Lockdown is in mode: {mode}. Found weak TLS on SSL policy: {ssl_policy}."
        # Publish message to Pub/Sub
        logging.info('Publishing message to Pub/Sub.')
        publish_message(project_id, message)
        if mode == "write":
            logging.info(f'Lockdown is in write mode. Updating SSL policy: {ssl_policy} with TLS 1.1."')
            update_ssl_policy(compute_client, ssl_description, project_id, ssl_policy)
        if mode == "read":
            logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f"The SSL policy {ssl_policy} is not using weak TLS.")

def get_ssl_policy(project_id, ssl_policy, compute_client):
    """
    Gets the minimum TLS version for the SSL policy.
    """

    # Get the SSL Policy metadata
    try:
        ssl_description = compute_client.sslPolicies().get(project=project_id, sslPolicy=ssl_policy).execute()
    except:
        logging.error(f"Could not get the SSL policy information from: {ssl_policy}.")
        raise
    
    return ssl_description

def analyze_ssl_policy(ssl_description, project_id, compute_client, ssl_policy):
    """
    Analyzes the SSL policy to see if the TLS version is 1.0.
    """

    # Extract the TLS version attached to the SSL Policy
    tls_version = ssl_description["minTlsVersion"]

    # Only return the tls_version variable if the SSL policy is using a weak version TLS 1.0
    if tls_version == "TLS_1_0":
        logging.info(f"SSL Policy: {ssl_policy} in project: {project_id} is using weak TLS version 1.0.")
        return tls_version
    else:
        logging.info(f"SSL policy {ssl_policy} in project: {project_id} is using: {tls_version}.")


def update_ssl_policy(compute_client, ssl_description, project_id, ssl_policy):
    """
    Updates the SSL policy to TLS 1.1. 
    TLS 1.0 is considered weak and should not be used.
    """

    # Update the SSL Policy to use TLS 1.1
    ssl_description['minTlsVersion'] = "TLS_1_1"

    try:
        compute_client.sslPolicies().patch(project=project_id, sslPolicy=ssl_policy, body=ssl_description).execute()
    except:
        logging.error(f"Could not update the SSL Policy: {ssl_policy}.")
        raise

def publish_message(project_id, message):
    """
    Publishes message to Pub/Sub topic for integration into alerting system.
    """

    # Create Pub/Sub Client
    pub_client = pubsub_v1.PublisherClient()

    try:
        topic_id = getenv('TOPIC_ID')
    except:
        logging.error('Topic ID not found in environment variable.')

    # Create topic object
    topic = pub_client.topic_path(project_id, topic_id)

    # Pub/Sub messages must be a bytestring
    data = message.encode("utf-8")

    try:
        pub_client.publish(topic, data)
        logging.info(f'Published message to {topic}')
    except:
        logging.error(f'Could not publish message to {topic_id}')
        raise

def create_service():
    """
    Creates the GCP Compute Service.
    """
    return googleapiclient.discovery.build('compute', 'v1', cache=MemoryCache())

def create_logger():
    """
    Integrates the Cloud Logging handler with the python logging module.
    """
    # Instantiates a cloud logging client
    client = glogging.Client()

    # Retrieves a Cloud Logging handler based on the environment
    # you're running in and integrates the handler with the
    # Python logging module
    client.get_default_handler()
    client.setup_logging()

class MemoryCache(Cache):
    """
    File-based cache to resolve GCP Cloud Function noisey log entries.
    """
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content
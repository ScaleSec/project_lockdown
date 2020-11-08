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
    Used with Pub/Sub trigger method to evaluate the GCE instance's service account.
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

    logging.info('Received GCE instance creation log from Pub/Sub. Checking for default service account.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)


    # Get the required API paramaters from log event
    ## instance_id contains our project, zone, and instance_name (all needed to make API calls)
    instance_id = log_entry['protoPayload']['resourceName']

    # Split the instance_id into a list of strings
    instance_list = instance_id.split('/')
    # Set our list of strings to remove
    remove_strings = ["projects", "zones", "instances"]
    # Remove all strings in list to get or variables
    project_zone_instance = [i for i in instance_list if i not in remove_strings]
    # Create the variables needed for API calls
    project_id = project_zone_instance[0]
    zone = project_zone_instance[1]
    instance_name = project_zone_instance[2]

    gce_info = get_gce_info(compute_client, instance_name, zone, project_id)

    gce_sa = eval_gce_info(gce_info, instance_name, zone, project_id)

    if gce_sa:
        # Set our pub/sub message
        message = f"Lockdown is in mode: {mode}. The GCE instance: {instance_name} in project: {project_id} is using the default compute service account."
        # Publish message to Pub/Sub
        logging.info(f'Publishing message to Pub/Sub.')
        publish_message(project_id, message)
        if mode == "write":
            logging.info(f"Lockdown is in write mode. Stopping the GCE instance {instance_name} in project {project_id}.")
            stop_gce_instance(compute_client, instance_name, zone, project_id)
        if mode == "read":
            logging.info(f"Lockdown is in read-only mode. Taking no action on the GCE instance: {instance_name} in project {project_id} for using the default compute service account. ")

def get_gce_info(compute_client, instance_name, zone, project_id):
    """
    Retrieves the GCE metadata.
    """

    try:
        gce_info = compute_client.instances().get(project=project_id, instance=instance_name, zone=zone).execute()
        logging.info(f"Getting GCE metadata from instance: {instance_name} in project: {project_id}.")
    except:
        logging.error(f"Could not get the GCE instance metadata from instance: {instance_name} in project: {project_id}.")
        raise
    
    return gce_info
    
def eval_gce_info(gce_info, instance_name, zone, project_id):
    """
    Determine the service account assigned to the GCE instance.
    """

    gce_sa = gce_info['serviceAccounts'][0]['email']

    if "developer.gserviceaccount.com" in gce_sa:
        logging.info(f"GCE instance: {instance_name} in project: {project_id} is using the default compute service account.")
        return gce_sa
    else:
        logging.info(f"GCE instance: {instance_name} in project: {project_id} is not using the default compute service account.")

def stop_gce_instance(compute_client, instance_name, zone, project_id):
    """
    Stops the GCE instance. Retries until success or exists after 5 attempts.
    """

    try:
        compute_client.instances().stop(project=project_id, instance=instance_name, zone=zone).execute()
        logging.info(f"GCE instance: {instance_name} in project: {project_id} stopped due to using the default compute service account.")
    except:
        logging.error(f"Could not stop the GCE instance: {instance_name} in project {project_id}.")
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

import base64
import json
import logging

from os import getenv
from googleapiclient.discovery_cache.base import Cache
import googleapiclient.discovery

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the GCE instance's service account.
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received GCE instance creation log from Pub/Sub. Checking for default service account.')

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    # Determine our Pub/Sub alerting topic
    try:
        topic_id = getenv('TOPIC_ID')
    except:
        logging.error('Topic ID not found in environment variable.')

    # Create compute client to make API calls
    compute_client = create_service()

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

    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info(f'The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.')

        # Retrieves the GCE metadata.
        gce_info = get_gce_info(compute_client, instance_name, zone, project_id)

        # Determine the service account assigned to the GCE instance.
        gce_sa = eval_gce_info(gce_info, instance_name, project_id)

        if gce_sa:
            finding_type = "gce_default_sa"
            # Set our pub/sub message
            message = f"The GCE instance: {instance_name} in project: {project_id} is using the default compute service account."
            # Publish message to Pub/Sub
            logging.info(f'Publishing message to Pub/Sub.')
            try:
                publish_message(finding_type, mode, instance_name, project_id, message, topic_id)
                logging.info(f'Published message to {topic_id}')
            except:
                logging.error(f'Could not publish message to {topic_id}')
                raise
            if mode == "write":
                logging.info(f"Lockdown is in write mode. Stopping the GCE instance {instance_name} in project {project_id}.")
                stop_gce_instance(compute_client, instance_name, zone, project_id)
            if mode == "read":
                logging.info(f"Lockdown is in read-only mode. Taking no action on the GCE instance: {instance_name} in project {project_id} for using the default compute service account. ")
    else:
        logging.info(f'The project {project_id} is in the allowlist or is not in the denylist. No action being taken.')

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

def eval_gce_info(gce_info, instance_name, project_id):
    """
    Determine the service account assigned to the GCE instance.
    """

    gce_sa = gce_info['serviceAccounts'][0]['email']

    if "compute@developer.gserviceaccount.com" in gce_sa:
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

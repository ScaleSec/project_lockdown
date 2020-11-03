import base64
import json
import logging

from os import getenv
from google.cloud import bigquery
from google.cloud import logging as glogging
from google.cloud import pubsub_v1

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the BigQuery Dataset for public members.
    """

    # Determine if CFN is running in view-only mode
    try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')

    #Create BigQuery Client
    client = bigquery.Client()

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info('Received BigQuery permissions update log from Pub/Sub. Checking for public access.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Get dataset ID and project ID from log event
    dataset_log = log_entry['resource']['labels']['dataset_id']
    project_id = log_entry['resource']['labels']['project_id']

    #Create dataset_ref
    dataset_id = project_id + "." + dataset_log
    
    try:
        # Create Dataset object
        dataset = client.get_dataset(dataset_id)
    except:
        logging.info(f'Could not access BigQuery Dataset {dataset_id}')

    # Evaluate the dataset
    private_access_entry = eval_dataset(dataset, dataset_log, project_id)

    if private_access_entry:
        # Set our pub/sub message
        message = f"Lockdown is in mode: {mode}. Found public members on dataset: {dataset_id} in project: {project_id}."
        # Publish message to Pub/Sub
        logging.info(f'Publishing message to Pub/Sub.')
        publish_message(project_id, message)
        # if the function is running in "write" mode, remove public members
        if mode == "write":
            logging.info('Lockdown is in write mode. Removing public IAM members from dataset.')
            # Remove public members
            update_dataset(client, private_access_entry, dataset_log, dataset)
        # if function is in read mode, take no action and publish message to pub/sub
        if mode == "read":
            logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f'No public members found. Taking no action on {dataset_id}')


def eval_dataset(dataset, dataset_log, project_id):
    """
    Check the BigQuery Dataset Access Entries to see if public members exist.
    """

    private_access_entry = []
    access_entries_list = list(dataset.access_entries)

    public_user1 = {'iamMember': 'allUsers'}
    public_user2 = {'specialGroup': 'allAuthenticatedUsers'}

    for entry in access_entries_list:
        # Convert each Access Entry into a dictionary
        entry_dict = entry.to_api_repr()
        if public_user1.items() <= entry_dict.items():
            logging.info('Public IAM member "allUsers" found.')
        elif public_user2.items() <= entry_dict.items():
            logging.info('Public IAM member "allAuthenticatedUsers" found.')
        else:
            private_access_entry.append(entry)
    
    # Compare Original Access Entry to new by looking at their lengths
    private_access_list = list(private_access_entry)
    if len(access_entries_list) != len(private_access_list):
        logging.info(f'Public IAM members found on dataset: {dataset_log} in project: {project_id}. A new BigQuery Dataset private Access Entry list is ready to be applied.')
        return private_access_entry
    else:
        logging.info('No public IAM members found. BigQuery Dataset is private.')

def update_dataset(client, private_access_entry, dataset_log, dataset):
    """
    Updates the Public BigQuery Dataset with a new access entry list.
    """

    # Convert to BigQuery Dataset attribute
    dataset.access_entries = private_access_entry

    try:
        client.update_dataset(dataset, ["access_entries"]) 
        logging.info(f'The BigQuery Dataset: {dataset_log} has been updated.')
    except:
        logging.error(f'Failed to update the BigQuery Dataset: {dataset_log}')
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
import base64
import json
import logging

from os import getenv
from google.cloud import bigquery
from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the BigQuery Dataset for public members.
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

    #Create BigQuery Client
    client = bigquery.Client()

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info('Received BigQuery permissions update log from Pub/Sub. Checking for public access.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Get dataset ID and project ID from log event
    dataset_id = log_entry['protoPayload']['resourceName']
    project_id = log_entry['resource']['labels']['project_id']
    # resource_id is passed to Pub/Sub 
    resource_id = dataset_id

    # Create the fully-qualified dataset ID in standard SQL format
    # Split the dataset_id into a list of strings
    dataset_list = dataset_id.split('/')
    # Set our list of strings to remove
    remove_strings = ["projects", "datasets"]
    # Remove all strings in list to create a list of dataset_id values
    dataset_id = [i for i in dataset_list if i not in remove_strings]
    dataset_name = dataset_id[1]
    # Create the fully-qualified dataset ID in standard SQL format using the leftover values
    dataset_id = '.'.join(dataset_id)

    try:
        # Create Dataset object
        dataset = client.get_dataset(dataset_id)
    except:
        logging.info(f'Could not access BigQuery Dataset {dataset_id}')

    # Evaluate the dataset
    private_access_entry = eval_dataset(dataset, dataset_name, project_id)

    if private_access_entry:
        finding_type = "public_bigquery_dataset"
        # Set our pub/sub message
        message = f"Found public members on bigquery dataset: {dataset_name} in project: {project_id}."
        # Publish message to Pub/Sub
        logging.info(f'Publishing message to Pub/Sub.')
        try:
            publish_message(finding_type, mode, resource_id, project_id, message, topic_id)
            logging.info(f'Published message to {topic_id}')
        except:
            logging.error(f'Could not publish message to {topic_id}')
            raise
        # if the function is running in "write" mode, remove public members
        if mode == "write":
            logging.info('Lockdown is in write mode. Removing public IAM members from dataset.')
            # Remove public members
            update_dataset(client, private_access_entry, dataset_name, dataset)
        # if function is in read mode, take no action and publish message to pub/sub
        if mode == "read":
            logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f'No public members found. Taking no action on BigQuery dataset: {dataset_name}')


def eval_dataset(dataset, dataset_name, project_id):
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
            logging.info(f"Public IAM member: allUsers found on dataset: {dataset_name} in project: {project_id}.")
        elif public_user2.items() <= entry_dict.items():
            logging.info(f"Public IAM member: allAuthenticatedUsers found on dataset: {dataset_name} in project: {project_id}.")
        else:
            private_access_entry.append(entry)
    
    # Compare Original Access Entry to new by looking at their lengths
    private_access_list = list(private_access_entry)
    if len(access_entries_list) != len(private_access_list):
        logging.info(f'Public IAM members found on dataset: {dataset_name} in project: {project_id}. A new BigQuery Dataset private Access Entry list is ready to be applied.')
        return private_access_entry
    else:
        logging.info(f"No public IAM members found. BigQuery Dataset: {dataset_name} is private.")

def update_dataset(client, private_access_entry, dataset_name, dataset):
    """
    Updates the Public BigQuery Dataset with a new access entry list.
    """

    # Convert to BigQuery Dataset attribute
    dataset.access_entries = private_access_entry

    try:
        client.update_dataset(dataset, ["access_entries"]) 
        logging.info(f'The BigQuery Dataset: {dataset_name} has been updated.')
    except:
        logging.error(f'Failed to update the BigQuery Dataset: {dataset_name}')
        raise

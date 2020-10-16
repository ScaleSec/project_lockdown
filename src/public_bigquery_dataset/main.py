import base64
import json
import logging

from google.cloud import bigquery
from google.cloud import logging as glogging

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the BigQuery Dataset for public members.
    """

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
        logging.info('Could not access BigQuery Dataset {}'.format(dataset_id))

    # Evaluate the dataset
    private_access_entry = eval_dataset(dataset)

    if private_access_entry:
        update_dataset(client, private_access_entry, dataset)
    else:
        logging.info('No public members found. Taking no action on {}'.format(dataset_id))


def eval_dataset(dataset):
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
        logging.info('A new BigQuery Dataset Access Entry list is ready to be applied.')
        return private_access_entry
    else:
        logging.info('No public IAM members found. BigQuery Dataset is private.')

def update_dataset(client, private_access_entry, dataset):
    """
    Updates the Public BigQuery Dataset with a new access entry list.
    """

    # Convert to BigQuery Dataset attribute
    dataset.access_entries = private_access_entry

    try:
        client.update_dataset(dataset, ["access_entries"]) 
        logging.info('The BigQuery Dataset {} has been updated.'.format(dataset))
    except:
        logging.error('Failed to update the BigQuery Dataset {}'.format(dataset))
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
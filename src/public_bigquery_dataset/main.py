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
    dataset = log_entry['resource']['labels']['dataset_id']
    project_id = log_entry['resource']['labels']['project_id']

    #Create dataset_ref
    dataset_id = project_id + "." + dataset

    # Create Dataset object
    dataset = client.get_dataset(dataset_id) 

    # Get Dataset Access entry
    access_entries = dataset.access_entries
    print(access_entries)


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
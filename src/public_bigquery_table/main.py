import base64
import json
import logging

from google.cloud import bigquery
from google.cloud import logging as glogging

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the BigQuery Table for public members.
    """

    #Create BigQuery Client
    client = bigquery.Client()

    # Integrates cloud logging handler to python logging
    create_logger()

    logging.info('Received BigQuery permissions update log from Pub/Sub. Checking for public access.')

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Create the fully-qualified table ID in standard SQL format
    # Split the table_id into a list of strings
    table_list = table_id.split('/')
    # Set our list of strings to remove
    remove_strings = ["projects", "datasets", "tables"]
    # Remove all strings in list to create a list of table_id values
    table_id = [i for i in table_list if i not in remove_strings]
    # Create the fully-qualified table ID in standard SQL format using the leftover values
    table_id = '.'.join(table_id)

    # Get the table ref
    table_ref = client.get_table(table_id)

    # Get the current BigQuery Table Policy
    table_policy = get_table_policy(client, table_ref)

    validate_table_policy(table_policy)


def get_table_policy(client, table_id):
    """
    Gets the BigQuery Table ACL / IAM Policy.
    """

    # We need to get the new table policy each time due to the unique etag
    table_policy = client.get_iam_policy(table_ref)

    table_policy_json = table_policy.to_api_repr()

    return table_policy_json

def validate_table_policy(table_policy):
    """
    Checks for public IAM members in a BigQuery table IAM policy.
    """

def update_table_policy()

def set_table_policy()



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


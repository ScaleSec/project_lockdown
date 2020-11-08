import base64
import json
import logging

from os import getenv
from google.cloud import bigquery
from google.cloud import logging as glogging
from google.cloud import pubsub_v1

def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the BigQuery Table for public members.
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

    # Get table resource ID from log entry

    table_id = log_entry['protoPayload']['serviceData']['setIamPolicyRequest']['resource']
    project_id = log_entry['resource']['labels']['project_id']

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

    # Generate a new policy without public members
    new_policy = validate_table_policy(table_policy, table_id)

    if new_policy:
        logging.info(f'Found public members on BQ table: {table_id}.')
        # Set our pub/sub message
        message = f"Lockdown is in mode: {mode}. Found public members on BigQuery table: {table_id}."
        # Publish message to Pub/Sub
        logging.info(f'Publishing message to Pub/Sub.')
        publish_message(project_id, message)
        if mode == "write":
            logging.info(f'Lockdown is in write mode. Updating BigQuery table: {table_id} with new table policy.')
            # Updates BQ table with private table policy
            update_table_policy(new_policy, client, table_ref, table_id)
        if mode == "read":
            logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f"The BigQuery Table: {table_id} is not public facing.")


def get_table_policy(client, table_ref):
    """
    Gets the BigQuery Table ACL / IAM Policy.
    """

    # Get the current IAM table policy (table ACL)
    table_policy = client.get_iam_policy(table_ref)

    return table_policy

def validate_table_policy(table_policy, table_id):
    """
    Checks for public IAM members in a BigQuery table IAM policy.
    """

    # Create the public users list to reference when creating new members.
    public_users = ["allAuthenticatedUsers", "allUsers"]

    # Create our new bindings
    bindings = []

    # table_policy is an IAM Policy class and has the bindings attribute
    for binding in table_policy.bindings:
        # Creates our members list for each IAM binding
        members = binding.get("members")
        # Check to see if there is an IAM policy directly attached to BQ table.
        # Inherited bindings do not display here. Only ones directly attached
        if members:
            # Reference our public users list and remove from members
            members = {i for i in members if i not in public_users}
            # Create a new binding using the same role and updated members list
            new_binding = {
                "role": binding["role"],
                "members": sorted(members)
            }
            # Use the same condition on mew IAM binding
            condition = binding.get("condition")
            if condition:
                new_binding["condition"] = condition
            # Add our new binding to the bindings variable for the new policy
            bindings.append(new_binding)
        else:
            logging.info(f'No IAM bindings found on BQ table: {table_id}.')
    # Set the new bindings entry using the updated bindings variable
    table_policy.bindings = bindings

    return table_policy

def update_table_policy(new_policy, client, table_ref, table_id):
    """
    Updates the BigQuery table with the new private IAM policy
    """

    try:
        client.set_iam_policy(table_ref, new_policy)
        logging.info(f"IAM policy successfully updated on BigQuery Table: {table_id}.")
    except:
        logging.error(f'Cannot update BQ table: {table_id}.')
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

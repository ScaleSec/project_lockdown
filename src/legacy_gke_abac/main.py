import base64
import json
import logging

from os import getenv
from google.cloud import container
from google.api_core import exceptions
from google.api_core import retry

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """
    Used with Pub/Sub trigger method to evaluate the GKE cluster for legacy ABAC.
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info('Received GKE cluster log from Pub/Sub. Checking for legacy ABAC.')

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

    # Determine alerting Pub/Sub topic
    try:
        alert_project = getenv('ALERT_GCP_PROJECT')
    except:
        logging.error('GCP alert project not found in environment variable.')

    # Create our GKE client
    container_client = container.ClusterManagerClient()

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Set our Cloud Logging variables
    cluster_id = log_entry['protoPayload']['resourceName']
    project_id = log_entry['resource']['labels']['project_id']
    cluster_name = log_entry['resource']['labels']['cluster_name']
    api_action = log_entry['protoPayload']['methodName']

    # Check our project_id against the project list set at deployment
    if check_list(project_id):
        logging.info(f'The project {project_id} is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.')

        # There are two different log events this function can be triggered with.
        # One is the creation of a cluster in which we need to get the clusters data.
        if api_action == "google.container.v1beta1.ClusterManager.CreateCluster":
            # Get cluster details to begin evaluation logic
            cluster_details = get_cluster_details(container_client, cluster_id)
            # Check to see if legacy ABAC is enabled
            abac_value = check_legacy_abac(cluster_details, cluster_id)
        # The other log event is when a cluster's legacy auth setting is updated
        # we can get enabled or disabled from the log event and do not need to get the cluster details
        # This cloud function shouldn't be invocated if the API event was to disable legacy ABAC
        # The logic below will always be set to enabled == true unless the log sink query is changed
        # By adding this check we can skip getting the clusters data and go right to disable_legacy_abac()
        if api_action == "google.container.v1.ClusterManager.SetLegacyAbac":
            logging.info(f"GKE cluster: {cluster_name} was updated to enable legacy ABAC.")
            abac_value = "enabled"

        if abac_value:
            finding_type = "gke_legacy_abac"
            # Set our pub/sub message
            message = f"GKE cluster: {cluster_id} has legacy ABAC enabled."
            # Publish message to Pub/Sub
            logging.info('Publishing message to Pub/Sub.')
            try:
                publish_message(finding_type, mode, cluster_name, alert_project, project_id, message, topic_id)
                logging.info(f'Published message to {topic_id}')
            except:
                logging.error(f'Could not publish message to {topic_id}')
                raise
            if mode == "write":
                logging.info("Lockdown is in write mode.")
                # update GKE cluster
                disable_legacy_abac(container_client, cluster_id)
            if mode == "read":
                logging.info('Lockdown is in read-only mode. Taking no action.')
    else:
        logging.info(f'The project {project_id} is in the allowlist or is not in the denylist. No action being taken.')


def get_cluster_details(container_client, cluster_id):
    """
    Gets the GKE cluster's metadata.
    This is passed to check_legacy_abac to validate the configuration.
    """
    try:
        cluster_details = container_client.get_cluster(name=cluster_id)
        return cluster_details
    except:
        logging.error(f"Cloud not get GKE cluster: {cluster_id} details.")
        raise

def check_legacy_abac(cluster_details, cluster_id):
    """
    Checks to see if Legacy ABAC is enabled.
    We want to disable this in disable_legacy_abac because it is insecure.

    ## Vars ##
    - abac_value
        This variable's value will either be enabled or empty.
        If empty, ABAC is not enabled and theres nothing to do.
        If enabled, we need to disable because ABAC is insecure.
    """

    abac_value = cluster_details.legacy_abac

    if abac_value:
        logging.info(f"GKE cluster {cluster_id} has legacy ABAC enabled.")
        return abac_value
    else:
        logging.info(f"Legacy ABAC is disabled for GKE cluster: {cluster_id}. No action needed.")


def disable_legacy_abac(container_client, cluster_id):
    """
    Disables legacy ABAC on the GKE cluster.

    ## Vars ##
    - my_retry
        GKE clusters do not accept updates during cluster creation.
        We set a retry value for the function to try every 10-30 seconds
        for a max duration of 5 minutes.
    """
    my_retry = retry.Retry(predicate=exceptions.FailedPrecondition, initial=10, maximum=30, deadline=300)

    try:
        logging.info(f"Disabling Legacy ABAC on GKE cluster: {cluster_id}.")
        # Make API call to disable ABAC
        container_client.set_legacy_abac(name=cluster_id, enabled=False, retry=my_retry)
        logging.info(f"Legacy ABAC disabled on GKE cluster: {cluster_id}.")
    # Attempt to catch precondition error if retry fails
    except exceptions.FailedPrecondition as precondition_err:
        logging.error(f"Could not update GKE cluster: {cluster_id}. Failed with error: {precondition_err}.")
    # Catches retry error when the 300 second deadline is hit
    except exceptions.RetryError as retry_err:
        logging.error(f"Could not update GKE cluster: {cluster_id}. Failed with error: {retry_err}.")
    except:
        logging.error(f"Could not update GKE cluster: {cluster_id}.")
        raise

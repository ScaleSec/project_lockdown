import base64
import json
import logging
import sys

from os import getenv
from google.cloud import artifactregistry
from google.api_core import exceptions # pylint: disable=import-error

from lockdown_logging import create_logger # pylint: disable=import-error
from lockdown_pubsub import publish_message # pylint: disable=import-error
from lockdown_checklist import check_list # pylint: disable=import-error


def pubsub_trigger(data, context):
    """Used with Pub/Sub trigger method to evaluate artifact registry resources
        for public access and remediate if public access exists.

    Args:
        data: Contains the Pub/Sub message
        context: The Cloud Functions event metdata
    """

    # Integrates cloud logging handler to python logging
    create_logger()
    logging.info(
        "Received Artifact Registry repository update log from Pub/Sub. Checking for public access.."
    )

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

    # Converting log to json
    data_buffer = base64.b64decode(data['data'])
    log_entry = json.loads(data_buffer)

    # Used for checking the allow/denylist
    project_id = log_entry['resource']['labels']['project_id']

    # The full registry name is commonly used for API calls
    registry_resource_name = log_entry["protoPayload"]["request"]["resource"]

    # This variable contains the current list of public IAM members in GCP
    public_users = ["allUsers", "allAuthenticatedUsers"]

    # Create the artifact registry client
    client = artifactregistry.ArtifactRegistryClient()

    # Check our project_id against the allow/denylist
    if check_list(project_id):
        logging.info(
            "The project %s is not in the allowlist, is in the denylist, or a list is not fully configured. Continuing evaluation.",
            project_id
        )

        # Get the artifact registry repository IAM  policy
        artifact_policy = get_artifact_policy(client, registry_resource_name)

        # Checks the artifact registry repository IAM policy for public members
        public_members = check_for_public_members(artifact_policy, public_users, registry_resource_name)

        # If a public member was found
        if public_members:
            finding_type = "public_artifact_repo"
            # Set our pub/sub message
            message = f"Found public members on the artifact registry repo: {registry_resource_name}."
            # Publish message to Pub/Sub
            logging.info('Publishing message to Pub/Sub.')
            try:
                publish_message(finding_type, mode, registry_resource_name, project_id, message, topic_id)
                logging.info(f'Published message to {topic_id}')
            except:
                logging.error(f'Could not publish message to {topic_id}')
                raise

            # if the function is running in "write" mode, remove public members
            if mode == "write":
                logging.info(
                    "Lockdown is in write mode. Removing public IAM members from artifact registry repo."
                )
                # create new private policy
                private_policy = remove_public_members(artifact_policy, public_users)
                # Update the artifact registry repository with the private IAM resource policy
                update_artifact_policy(client, private_policy, registry_resource_name)

            # if function is in read mode, take no action and publish message to pub/sub
            if mode == "read":
                logging.info(
                    "Lockdown is in read-only mode. Taking no action."
                )

        else:
            logging.info(
                "No public members found on %s",
                registry_resource_name
            )

    else:
        logging.info(
            "The project %s is in the allowlist or is not in the denylist. No action being taken.",
            project_id
        )


def get_artifact_policy(client, registry_resource_name):
    """Gets the IAM policy attached to the Artifact Registry
        repository that generated the Cloud Logging event.

    Args:
        client: Artifact registry client.
        registry_resource_name ([str]): The full resource name
                                        of the artifact registry repository.

    Returns:
        [object]: The IAM resource policy
                for the artifact registry repository.
    """

    # Create the GetIamPolicyRequest GCP class object
    # which is required by the method get_iam_policy()
    repo = {
        "resource": registry_resource_name
    }

    # Using the created class object above
    # Get the IAM policy attached to the artifact repository
    try:
        logging.info(
            "Getting IAM policy from %s",
            registry_resource_name
        )
        artifact_policy = client.get_iam_policy(repo)
    except exceptions.PermissionDenied as perm_error:
        logging.error(
            "Error \"%s\" while retrieving the IAM resource policy for artifact repo \"%s\".",
            perm_error.grpc_status_code.name,
            registry_resource_name
        )
        sys.exit(1)

    logging.info(
            "IAM policy successfully retrieved."
        )

    return artifact_policy


def check_for_public_members(artifact_policy, public_users, registry_resource_name):
    """Checks the IAM policy in question for "public" IAM members.
        Example public members include "allUsers" and "allAuthenticatedUsers".

    Args:
        artifact_policy ([list]): A collection of IAM bindings
                                on the artifact repository resource.
        public_users ([list]): A list of all IAM members in GCP
                            that are considered public.
        registry_resource_name ([str]): The full resource name
                                        of the artifact registry repository.

    Returns:
        [bool]: True if there are public members
                in the IAM resource policy.
    """

    logging.info(
            "Checking for public members.."
        )
    # For each binding in the resource policy
    for binding in artifact_policy.bindings:
        # binding.members can be a list of members
        #   if multiple IAM members have the same IAM role
        # For each member in the IAM binding
        for member in binding.members:
            # Check to see if member is public
            if member in public_users:
                logging.info(
                    "Artifact registry repository \"%s\" has at least one public member!",
                    registry_resource_name
                )
                return True #TODO: do we just call remove?
            else:
                logging.debug("IAM binding member is not public.")

def remove_public_members(artifact_policy, public_users):
    """Removes the public IAM members from the IAM policy.

    Args:
        artifact_policy ([list]): A collection of IAM bindings
                                    on the artifact repository resource.
        public_users ([list]): A list of all IAM members in GCP
                                that are considered public.

    Returns:
        [list]: A private IAM policy for an artifact registry repository.
    """

    logging.info(
            "Generating a new private-only IAM resource policy..",
        )
    # For each binding in the resource policy
    for binding in artifact_policy.bindings:
        # binding.members can be a list of members
        #   if multiple IAM members have the same IAM role
        # For each member in the IAM binding
        for member in binding.members:
            # Check to see if member is public
            if member in public_users:
                logging.info(
                    "Removing public IAM member \"%s\".",
                    member
                )
                # Remove the public member from the IAM binding
                binding.members.remove(member)
            else:
                logging.debug("IAM binding member is not public.")

    return artifact_policy

def update_artifact_policy(client, private_policy, registry_resource_name):
    """[summary]

    Args:
        client: Artifact registry client.
        private_policy ([list]): A private IAM policy
                                for an artifact registry repository.
        registry_resource_name ([str]): The full resource name
                                        of the artifact registry repository.
    """

    # Create the SetIamPolicyRequest GCP class object
    # which is required by the method set_iam_policy()
    repo = {
        "resource": registry_resource_name,
        "policy": private_policy
    }

    # Update the public artifact registry repository
    # with a private IAM policy
    try:
        logging.info("Updating IAM policy on artifact repo \"%s\"..")
        client.set_iam_policy(repo)
    except exceptions.PermissionDenied as perm_error:
        logging.error(
            "Error \"%s\" while updating the IAM resource policy for artifact repo \"%s\".",
            perm_error.grpc_status_code.name,
            registry_resource_name
        )
        sys.exit(1)

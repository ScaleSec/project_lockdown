# Development Guide

Thank you for your interest in contributing to Project Lockdown. This guide will provide you with general guidance on how to create automated remediation Cloud Functions. Before beginning development, make sure you have read through our [contributing guidelines](CONTRIBUTING.md).

## Data Flow

Potential remediation events in Project Lockdown follow a standardized data flow. Cloud Logging has a feature called [aggregated log sinks](https://cloud.google.com/logging/docs/export/aggregated_sinks) that Project Lockdown deploys on the organization level of your environment's resource hierarchy. This allows Lockdown to catch any event in every project that matches it's [filter](https://cloud.google.com/logging/docs/export/aggregated_sinks#aggregated-filters). 

Once a potential remediation event is matched to the log sink's filter, it is sent to a Pub/Sub topic. Each remediation function has it's own Pub/Sub topic that it subscribes to for messages. Once a message (Cloud Logging event) lands in a Pub/Sub topic, Pub/Sub will automatically trigger the remediation Cloud Function subscribed to the topic to analyze the GCP resource in question. More information about Pub/Sub subscriptions can be found [here](https://cloud.google.com/pubsub/docs/subscriber).

The remediation Cloud Function will analyze the GCP resource related to the Cloud Logging event and determine if the resource is in violation of best practices. If Project Lockdown is deployed in `write` mode, the Cloud Function will remediate the resource and log a message to an alerting Pub/Sub topic. This Pub/Sub topic is separate from the topic that the Cloud Function receives it's messages from, is shared by all Cloud Functions in Project Lockdown, and is available for you to tie in a SIEM or alerting functionality. If the Cloud Function is in `read` mode (default), the function will not update the resource and will only log a message to the alerting Pub/Sub topic.

## Terraform Requirements

Project Lockdown is written using the new `for_each` (v.13 of Terraform) module functionality to reduce the amount of Terraform updates required when a new remediation is configured. If you are interested in adding a new Cloud Function to remediate a specific scenario you will need to perform the following.

1. Add a new JSON block to the [terraform.tfvars](../terraform.tfvars) file and match the structure of the previous entries. For example:

```
enabled_modules = {
#   public_bigquery_dataset = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "bqdataset",
#     log_sink_filter = "resource.type=\"bigquery_dataset\"  protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get", "pubsub.topics.publish"],
#   }
#   $new_remediation_here = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "$your_name_prefix_here",
#     log_sink_filter = "$your_filter_here"
#     function_perms = $your_permissions_here,
#   }
```
__Do not add sensitive information to the `.tfvars` file.__

2. The `name` variable represents a prefix that is added to GCP resources. We suggest keeping it short and avoiding dashes, underscores, or special characters. 
3. The `log_sink_filter` is the aggregated log sink filter. This should be as specific as possible to reduce the number of invocations of the Cloud Function. Make sure to include the literal value of: __AND NOT protoPayload.authenticationInfo.principalEmail__ in your filter query so that Lockdown does not invocate based on its own actions.
4. The `function_perms` is the Cloud Functions custom role permissions. Try to keep this as close to least privilege as possible and you must include `"logging.logEntries.create"` and `"pubsub.topics.publish"` so that the function can log and publish messages to the alerting Pub/Sub topic.
5. `function_memory` is an optional variable that can be assigned per function. The default is 128, but if a function requires more memory, it can be specified in `.tfvars` like `function_memory = 256`

## Cloud Function Requirements

All of the Cloud Functions are written in python 3.8 and leverage shared functions located in the [src](../src/common/) directory. In order to start to create the evaluation logic for a remediation, you first need to create a directory in the [src](../src/) folder that matches the name you selected in step 2 in the Terraform Requirements above.

Inside your `src/` folder, you need a `requirements.txt`, `main.py`, and an empty `__init__.py`. The `requirements.txt` contains all of your external packages needed.

## Python Requirements

### Accepting Pub/Sub message
Python Cloud Functions that are triggered via a Pub/Sub topic need to be formatted in a way to parse the log event. We recommend using the same entry point as other functions:

```
def pubsub_trigger(data, context):
    """
   $your_docstring_here
    """
```

### Function Logging
In order to support robust logging inside the Cloud Function, we import the shared function `from lockdown_logging import create_logger` and call that function in our entry point:

```
# Integrates cloud logging handler to python logging
    create_logger()
```

Once you have the proper logging configured you can easily create logs in Cloud Logging using `logging.$loglevel("Log message here)`. An example could be `logging.info("Log received from Pub/Sub.")`. 

### Pub/Sub messages
Similiar to the function logging outlined above, we use a shared function that is imported via `from lockdown_pubsub import publish_message`. This function requires six arguments:

```
publish_message(finding_type, mode, resource_id, project_id, message_info, topic_id)
```

1. Two of the arguments, `mode` and `topic_id` you can retrieve from the Cloud Functions environment variables:

```
try:
        mode = getenv('MODE')
    except:
        logging.error('Mode not found in environment variable.')
    
    # Determine alerting Pub/Sub topic
    try:
        topic_id = getenv('TOPIC_ID')
    except:
        logging.error('Topic ID not found in environment variable.')
```
2. `finding_type` generally aligns with the `src/` sub-directory name you created but is intended to identity _what_ was found. `public_bugquery_dataset` is an example of a `finding_type`.
3. `resource_id` represents the GCP resource that is being analyzed. 
4. `project_id` is the GCP project where the resource in question lives.
5. `message_info` is a sentence about what was discovered. An example could be `A Public BigQuery dataset was discovered`.

## Additional Information
Other than what was outlined above we only request that you diligently use `try` and `except` error handling and log as much as possible. We are currently in the process of improving our unit test coverage so please try to add unit tests as well. 

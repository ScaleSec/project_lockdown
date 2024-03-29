# Project Lockdown

![Lockdown Banner](./img/lockdown_banner.png)


![Code Coverage](./.coverage.svg) [![GitHub Super-Linter](https://github.com/ScaleSec/project_lockdown/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)

## Introduction
Project Lockdown is a collection of serverless event-driven auto remediation Cloud Functions designed to react to unsecure resource creations or configurations. Project Lockdown is meant to be deployed in a GCP environment and has the capabilities to monitor and remediate across your entire Organization hierarchy in a matter of seconds.

## Why is this needed?
Project Lockdown was born out of a common theme from our customers - there are certain configurations or events that they do not want to happen but there are currently no provider-native controls available to prevent these actions. For example, making a [GCS bucket](https://cloud.google.com/storage/docs/access-control/making-data-public) or [BigQuery dataset](https://cloud.google.com/bigquery/docs/datasets-intro) that stores sensitive information public puts your data at risk and it can only take minutes for malicious individuals to find those resources and exfiltrate data.

There are compensating controls like the Organization Policy [constraint](https://cloud.google.com/resource-manager/docs/organization-policy/org-policy-constraints) `constraints/iam.allowedPolicyMemberDomains` that attempt to prevent GCS buckets from being made public but have potentially negative side effects. Organizations must constantly keep a running list of Google Workspace IDs (formally G Suite) and also track where and when hierarchies are broken which adds operational overhead.

Project Lockdown aims to be a safe, lightweight, and inexpensive tool to increase your security posture.

## How does it work?
Project Lockdown works by using a very efficient data flow that takes advantage of GCP's [Cloud Logging](https://cloud.google.com/logging/docs/basic-concepts) advanced query log sinks. By configuring a filter (query) as specific as possible on the log sink, Project Lockdown will only invocate a Cloud Function when necessary to remediate events deemed high risk or unsecure.

When a target event is captured by the log sink it is sent to a Cloud Pub/Sub topic that triggers a Cloud Function automatically. This Cloud Function analyzes the event payload and extracts the data necessary for it to evaluate the current resource's configuration. If the Cloud Function determines that the resource is misconfigured according to its evaluation logic it will remediate the resource and reconfigure it in a safe manner. Typically, the action taken by the Cloud Function is a reversal of the event. If a bucket was made public, it is made private, but if a SSL policy is created using `TLS 1.0`, it will be updated to `TLS 1.1`.

## How can I trust this?
Trust is a key component of any security tool so Project Lockdown is built with that in mind. A few examples of this are:
- __Least privilege access.__ The Cloud Function that performs actions in your environment has only the permissions it needs to perform its programmed actions. No predefined roles are used and only custom purpose-driven roles are assigned.
- __Read-only by default.__ Project Lockdown will not take action in your environment unless you configure it to do so. Out of the box Project Lockdown is read only.
- __Isolated workloads.__ Each remediation use case or Cloud Function has it's own custom role, its own service account and its own separate Pub/Sub topic to receive events. The only shared resource between the different remediation modules is a Pub/Sub topic where you can subscribe to for alerts.

## Alerting
Project Lockdown will submit a message to a Pub/Sub topic for each finding it encounters. Slack, SendGrid, JIRA, or even a SIEM can be subscribed to the Pub/Sub topic to receive alerts. Regardless if Project Lockdown is in read or write mode, a message will be published in addition to Cloud Logging events for each action taken.

## Allowlist or Denylist functionality
Project Lockdown supports an allowlist or denylist on a per remediation basis or one to cover all remediations. To configure an allowlist or denylist follow the below steps:

- Set the `list_type` variable to either `allow` or `deny` depending on the type of list you'd like. You can set this inside each `enabled_modules` key or outside (to apply to all remediations).
- Supply a list of comma separated (no spaces) project IDs enclosed by double quotes to the variable `project_list`. For example: "project123,projectabc,project-1"

## Remediation Scenarios
For details around what scenarios Project Lockdown remediates, view the [documentation](./src/README.md).

## Log Filters
To view which log events Project Lockdown monitors for, view the [documentation](./docs/LOGFILTERS.md).

## Can I contribute or request features?
Project Lockdown is under active development and we welcome any questions, bug reports, feature requests or enhancements via a GitHub Issue or Pull Request. If you plan to contribute to Project Lockdown please follow our [Contribution Guidelines](docs/CONTRIBUTING.md) for suggestions and requirements.


## Usage

### Modes

Project Lockdown has the capability to run in two modes: `read` and `write`. In `write` mode, Project Lockdown will automatically remediate the findings it discovers. Both `read` and `write` modes will send an alert to a Pub/Sub topic to integrate into your alerting process.

### Requirements

* Docker
* Make
* Bash

### Local Testing

This will run the container with tests and generate code coverage.

```shell
make test
```

### Terraform

Project Lockdown is able to deploy many different remediation functions and their accompanying resources using the [module](https://learn.hashicorp.com/tutorials/terraform/for-each) `for_each` functionality. This allows us to only specify one `main.tf` in the [terraform](./terraform) directory but deploy as many copies as there are entries in the variable `enabled_modules`.

### Deployment

- Copy `terraform.tfvars` into a file that ends in `.auto.tfvars` and edit the `enabled_modules` variable as desired (remember to uncomment the necessary lines).
- To enable automatic remediation, be sure to set the `mode` variable as `write`
- We do not recommend updating the variables `log_sink_filter` or `function_perms` because those have been tailored to work with Project Lockdown.
- We DO recommend deploying all Lockdown resources into an isolated security project, including the Pub/Sub topic for alerts.

```bash
# To deploy Project Lockdown

# First initialize Terraform

terraform init

# Next, create a plan file

terraform plan -out tfplan.out

# Review the plan file and apply once satisfied

terraform apply "tfplan.out"
```

__Note: Functions not specified in `enabled_modules` will not be created and will be skipped.__

#### Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| alert\_topic\_project\_id | The project to deploy the alert Pub/Sub topic to. | `string` | n/a | yes |
| enabled\_modules | A mapping of enabled modules and their variables | `any` | n/a | yes |
| list\_type | The type of list being passed in to the Cloud Function. The choices are allow, deny, or N/A (for none). | `string` | `"N/A"` | no |
| mode | The mode to run lockdown in, either read or write. | `string` | `"read"` | no |
| org\_id | The Organization ID to monitor. | `any` | n/a | yes |
| project\_list | A list of project IDs to use as a denylist or allowlist. | `string` | `"N/A"` | no |
| region | The region to deploy lockdown resources to. | `string` | `"us-east1"` | no |
| risky\_roles | A list of IAM roles that are considered risky. This list is used to check IAM bindings against for the remediation protect\_lockdown\_sa | `string` | `"[\"roles/aiplatform.customCodeServiceAgent\", \"roles/aiplatform.serviceAgent\", \"roles/appengineflex.serviceAgent\", \"roles/bigquerydatatransfer.serviceAgent\", \"roles/cloudbuild.serviceAgent\", \"roles/clouddeploy.serviceAgent\", \"roles/cloudfunctions.serviceAgent\", \"roles/cloudscheduler.serviceAgent\", \"roles/cloudtasks.serviceAgent\", \"roles/cloudtpu.serviceAgent\", \"roles/composer.serviceAgent\", \"roles/compute.serviceAgent\", \"roles/container.serviceAgent\", \"roles/dataflow.serviceAgent\", \"roles/dataprep.serviceAgent\", \"roles/dataproc.hubAgent\", \"roles/dataproc.serviceAgent\", \"roles/editor\", \"roles/eventarc.serviceAgent\", \"roles/genomics.serviceAgent\", \"roles/iam.serviceAccountKeyAdmin\", \"roles/iam.serviceAccountTokenCreator\", \"roles/iam.serviceAccountUser\", \"roles/iam.workloadIdentityUser\", \"roles/lifesciences.serviceAgent\", \"roles/ml.serviceAgent\", \"roles/notebooks.serviceAgent\", \"roles/osconfig.serviceAgent\", \"roles/owner\", \"roles/pubsub.serviceAgent\", \"roles/run.serviceAgent\", \"roles/serverless.serviceAgent\", \"roles/sourcerepo.serviceAgent\", \"roles/workflows.serviceAgent\"]"` | no |
| rotation\_period | The approved rotation period, in days, for Cloud KMS keys. | `number` | `90` | no |
| topic\_name | The Pub/Sub topic to send messages to when a finding is generated. | `string` | `"project_lockdown_alert_topic"` | no |


## Limitation of Liability

Please view the [License](LICENSE) for limitations of liability.

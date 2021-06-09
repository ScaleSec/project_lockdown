variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "enabled_modules" {
  description = "A mapping of enabled modules and their variables"
  type        = any
}

variable "alert_topic_project_id" {
  description = "The project to deploy the alert Pub/Sub topic to."
  type        = string
}

variable "topic_name" {
  description = "The Pub/Sub topic to send messages to when a finding is generated."
  default     = "project_lockdown_alert_topic"
  type        = string
}

variable "mode" {
  type        = string
  default     = "read"
  description = "The mode to run lockdown in, either read or write."
}

variable "org_id" {
  description = "The Organization ID to monitor."
}

variable "list_type" {
  description = "The type of list being passed in to the Cloud Function. The choices are allow, deny, or N/A (for none)."
  type        = string
  default     = "N/A"
}

variable "project_list" {
  description = "A list of project IDs to use as a denylist or allowlist."
  type        = string
  default     = "N/A"
}

variable "rotation_period" {
  type        = number
  default     = 90
  description = "The approved rotation period, in days, for Cloud KMS keys."
}

variable "risky_roles" {
  type        = string
  default     = "[\"roles/aiplatform.customCodeServiceAgent\", \"roles/aiplatform.serviceAgent\", \"roles/appengineflex.serviceAgent\", \"roles/bigquerydatatransfer.serviceAgent\", \"roles/cloudbuild.serviceAgent\", \"roles/clouddeploy.serviceAgent\", \"roles/cloudfunctions.serviceAgent\", \"roles/cloudscheduler.serviceAgent\", \"roles/cloudtasks.serviceAgent\", \"roles/cloudtpu.serviceAgent\", \"roles/composer.serviceAgent\", \"roles/compute.serviceAgent\", \"roles/container.serviceAgent\", \"roles/dataflow.serviceAgent\", \"roles/dataprep.serviceAgent\", \"roles/dataproc.hubAgent\", \"roles/dataproc.serviceAgent\", \"roles/editor\", \"roles/eventarc.serviceAgent\", \"roles/genomics.serviceAgent\", \"roles/iam.serviceAccountKeyAdmin\", \"roles/iam.serviceAccountTokenCreator\", \"roles/iam.serviceAccountUser\", \"roles/iam.workloadIdentityUser\", \"roles/lifesciences.serviceAgent\", \"roles/ml.serviceAgent\", \"roles/notebooks.serviceAgent\", \"roles/osconfig.serviceAgent\", \"roles/owner\", \"roles/pubsub.serviceAgent\", \"roles/run.serviceAgent\", \"roles/serverless.serviceAgent\", \"roles/sourcerepo.serviceAgent\", \"roles/workflows.serviceAgent\"]"
  description = "A list of IAM roles that are considered risky. This list is used to check IAM bindings against for the remediation protect_lockdown_sa"
}

variable "lockdown_project" {
  description = "The GCP project to deploy lockdown resources to."
}

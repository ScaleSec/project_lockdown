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

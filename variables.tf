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

variable "allowlist" {
  description = "An allowlist of project IDs that should not have their action reverted."
  type = string
  default = "12345, 123"
}

variable "mode" {
  type        = string
  default     = "read"
  description = "The mode to run lockdown in, either read or write."
}

variable "org_id" {
  description = "The Organization ID to monitor."
}
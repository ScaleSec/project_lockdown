variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "enabled_modules" {
  description = "A mapping of enabled modules and their variables"
  type        = any
}

variable "project_id" {
  description = "The project to deploy the alert Pub/Sub topic to."
  type        = string
}

variable "topic_name" {
  description = "The Pub/Sub topic to send messages to when a finding is generated."
  default     = "project_lockdown_alert_topic"
  type        = string
}

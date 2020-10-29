variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "enabled_modules" {
  description = "A mapping of enabled modules and their variables"
  type        = any
}

variable "topic_project" {
  description = "The project to deploy the alert Pub/Sub topic to."
  type        = string
}
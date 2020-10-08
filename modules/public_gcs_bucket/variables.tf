
variable "org_id" {
  description = "The Organization ID to monitor."
}

variable "project" {
  description = "The GCP project to deploy lockdown resources to."
}

variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "name" {
  description = "A prefix for resource names."
  default     = "lckdn"
}

variable "org_sink_filter" {
  description = "The log filter to apply to the Org Level Cloud Logging export."
  default     = "" ## TODO
}

variable "function_perms" {
  description = "The Cloud Function Cloud IAM permissions."
  default     = "" ## TODO
}


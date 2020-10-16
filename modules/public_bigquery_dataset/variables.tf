
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

variable "function_perms" {
  type = list(string)
  description = "The Cloud Function Cloud IAM permissions."
  default     = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get"] ## TODO
}

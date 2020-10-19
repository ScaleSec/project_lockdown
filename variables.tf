variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "enabled_modules" {
  description = "A mapping of enabled modules and their variables"
  type = any
}
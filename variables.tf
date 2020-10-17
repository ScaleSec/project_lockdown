variable "region" {
  description = "The region to deploy lockdown resources to."
  default     = "us-east1"
}

variable "enabled_modules" {
  description = "A mapping of enabled modules and their variables"
  type = any
  # type     = object({
  #   module_name = map(object({
  #     org_id = string,
  #     project = string,
  #     region = string,
  #     name = string,
  #     function_perms = list(string),
  #     function_name = string
  #   }))
  # })
}

# variable "enabled_modules" {
#   description = "description"
#   type     = object({
#     org_id = string,
#     project = string,
#     region = string,
#     name = string,
#     function_perms = list(string)
#   })
# }
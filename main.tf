# TODO: put in a feature request for the below functionality

# module "function" {
#   for_each = var.enabled_modules
#   source   = "./modules/${each.key}"

#   org_id = lookup(each.value, "org_id")
#   project = lookup(each.value, "project")
#   region = lookup(each.value, "region")
#   name = lookup(each.value, "name")
#   function_perms = lookup(each.value, "function_perms")
# }

resource "google_pubsub_topic" "alerting_topic" {
  name    = var.topic_name
  project = var.alert_topic_project_id
}

module "project-services" {
  for_each = var.enabled_modules
  source   = "terraform-google-modules/project-factory/google//modules/project_services"
  version  = "4.0.0"

  project_id = lookup(each.value, "lockdown_project")

  activate_apis = [
    "iam.googleapis.com",
    "cloudfunctions.googleapis.com",
    "storage.googleapis.com",
    "pubsub.googleapis.com"
  ]
  disable_services_on_destroy = false
}

module "function" {
  for_each      = var.enabled_modules
  source        = "./terraform"
  function_name = each.key

  org_id           = var.org_id
  lockdown_project = lookup(each.value, "lockdown_project")
  region           = lookup(each.value, "region", var.region)
  mode             = lookup(each.value, "mode", var.mode)
  name             = lookup(each.value, "name")
  log_sink_filter  = lookup(each.value, "log_sink_filter")
  function_memory  = lookup(each.value, "function_memory", 128)
  function_perms   = lookup(each.value, "function_perms")
  topic_id         = google_pubsub_topic.alerting_topic.name
  project_list     = lookup(each.value, "allowlist", var.project_list)
  list_type        = lookup(each.value, "allowlist", var.list_type)
  rotation_period  = var.rotation_period
  risky_roles      = var.risky_roles
}

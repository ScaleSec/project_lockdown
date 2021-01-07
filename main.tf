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
  project = var.project_id
}

module "project-services" {
  source  = "terraform-google-modules/project-factory/google//modules/project_services"
  version = "4.0.0"

  project_id = var.project_id

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

  org_id          = lookup(each.value, "org_id")
  project         = lookup(each.value, "project")
  region          = lookup(each.value, "region")
  mode            = lookup(each.value, "mode")
  name            = lookup(each.value, "name")
  function_memory = lookup(each.value, "function_memory", 128)
  log_sink_filter = lookup(each.value, "log_sink_filter")
  function_perms  = lookup(each.value, "function_perms")
  topic_id        = google_pubsub_topic.alerting_topic.name
}

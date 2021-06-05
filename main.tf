
resource "google_pubsub_topic" "alerting_topic" {
  name    = var.topic_name
  project = var.alert_topic_project_id
}

module "project-services" {
  for_each = var.enabled_modules
  source   = "terraform-google-modules/project-factory/google//modules/project_services"
  version  = "4.0.0"

  project_id = lookup(each.value, "lockdown_project", var.lockdown_project)

  activate_apis = [
    "artifactregistry.googleapis.com",
    "bigquery.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudkms.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "iam.googleapis.com",
    "pubsub.googleapis.com",
    "storage.googleapis.com"
  ]
  disable_services_on_destroy = false
}

module "function" {
  for_each      = var.enabled_modules
  source        = "./terraform"
  function_name = each.key

  org_id                 = var.org_id
  lockdown_project       = lookup(each.value, "lockdown_project", var.lockdown_project)
  region                 = lookup(each.value, "region", var.region)
  mode                   = lookup(each.value, "mode", var.mode)
  name                   = lookup(each.value, "name")
  log_sink_filter        = lookup(each.value, "log_sink_filter")
  function_memory        = lookup(each.value, "function_memory", 128)
  function_perms         = lookup(each.value, "function_perms")
  topic_id               = google_pubsub_topic.alerting_topic.name
  project_list           = lookup(each.value, "allowlist", var.project_list)
  list_type              = lookup(each.value, "allowlist", var.list_type)
  alert_topic_project_id = var.alert_topic_project_id
  rotation_period        = var.rotation_period
  risky_roles            = var.risky_roles
}

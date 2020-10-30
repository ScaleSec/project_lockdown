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
  project = var.topic_project

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
  log_sink_filter = lookup(each.value, "log_sink_filter")
  function_perms  = lookup(each.value, "function_perms")
  topic_id        = google_pubsub_topic.alerting_topic.name
}

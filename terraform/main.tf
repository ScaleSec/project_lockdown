#####################
## Local variables ##
#####################

## Sets the Cloud Function name
locals {
  function_name    = "${lower(var.name)}-${var.function_name}_function_${random_id.random.hex}"
  function_sa_name = "${lower(var.name)}-sa"
  log_sink_filter  = "${var.log_sink_filter} = ${google_service_account.cfn_sa.email}"
  source_files     = ["src/${var.function_name}/main.py", "src/${var.function_name}/requirements.txt", "src/${var.function_name}/__init__.py", "src/common/__init__.py", "src/common/lockdown_logging.py", "src/common/lockdown_pubsub.py", "src/common/lockdown_allowlist.py"]

}

data "template_file" "function_file" {
  count    = length(local.source_files)
  template = file(element(local.source_files, count.index))
}

resource "local_file" "to_temp_dir" {
  count    = length(local.source_files)
  filename = "${path.module}/temp/${var.function_name}/${basename(element(local.source_files, count.index))}"
  content  = element(data.template_file.function_file.*.rendered, count.index)
}

####################
## Misc resources ##
####################

## Used as a unique name suffix for the deployment
resource "random_id" "random" {
  byte_length = 4
}

#########################
## Org level resources ##
#########################

## Org level Cloud Logging sink / export
resource "google_logging_organization_sink" "sink" {
  name             = "${lower(var.name)}-${var.function_name}_sink_${random_id.random.hex}"
  org_id           = var.org_id
  destination      = "pubsub.googleapis.com/projects/${var.project}/topics/${google_pubsub_topic.topic.name}"
  filter           = local.log_sink_filter
  include_children = true
}

## Org level custom Cloud IAM role
resource "google_organization_iam_custom_role" "custom_role" {
  role_id     = "${var.function_name}_custom_role"
  org_id      = var.org_id
  title       = "${var.function_name} Role"
  description = "Minimally privileged role to manage Resources."
  permissions = var.function_perms
}

## Org level Cloud IAM member binding
resource "google_organization_iam_member" "custom_role_member" {
  org_id = var.org_id
  role   = "organizations/${var.org_id}/roles/${google_organization_iam_custom_role.custom_role.role_id}"
  member = "serviceAccount:${google_service_account.cfn_sa.email}"
}

#############################
## Project level resources ##
#############################

## Cloud Function Service Account
resource "google_service_account" "cfn_sa" {
  project      = var.project
  account_id   = local.function_sa_name
  display_name = "${var.name} ${var.function_name} CFN SA"
}

## Pub/Sub Topic for log exports
resource "google_pubsub_topic" "topic" {
  name    = "${lower(var.name)}-${var.function_name}_topic"
  project = var.project
}

## Log sink Cloud IAM binding
resource "google_pubsub_topic_iam_member" "publisher" {
  project = var.project
  topic   = google_pubsub_topic.topic.name
  role    = "roles/pubsub.publisher"
  member  = google_logging_organization_sink.sink.writer_identity
}

## Cloud Function source file
data "archive_file" "source" {
  type        = "zip"
  output_path = "builds/${var.function_name}/${var.function_name}.zip"
  source_dir  = "${path.module}/temp/${var.function_name}"

  depends_on = [
    local_file.to_temp_dir,
  ]
}

## Cloud Function source bucket
resource "google_storage_bucket" "cfn_bucket" {
  project = var.project
  name    = "${lower(var.name)}-${var.function_name}_cfn_bucket_${var.project}"
}

## Cloud Function source file upload
resource "google_storage_bucket_object" "cfn_source_archive" {
  name   = "src-${lower(replace(base64encode(data.archive_file.source.output_md5), "=", ""))}.zip"
  bucket = google_storage_bucket.cfn_bucket.name
  source = data.archive_file.source.output_path
}

## Cloud Function
resource "google_cloudfunctions_function" "cfn" {
  name                  = local.function_name
  description           = "Cloud Function to remediate ${var.function_name}."
  project               = var.project
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.cfn_bucket.name
  source_archive_object = google_storage_bucket_object.cfn_source_archive.name
  timeout               = 300
  entry_point           = "pubsub_trigger"
  service_account_email = google_service_account.cfn_sa.email
  runtime               = "python38"

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.topic.name
  }

  environment_variables = {
    MODE     = var.mode
    TOPIC_ID = var.topic_id
    ALLOWLIST = var.allowlist
  }
}

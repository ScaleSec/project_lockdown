
#####################
## Local variables ##
#####################

## Sets the Cloud Function name
locals {
  function_name = "${lower(var.name)}-gcs_auto_remediate_function_${random_id.random.hex}"
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
resource "google_logging_organization_sink" "gcs_auto_remediate_sink" {
  name             = "${lower(var.name)}-gcs_auto_remediate_sink_${random_id.random.hex}"
  org_id           = var.org_id
  destination      = "pubsub.googleapis.com/projects/${var.project}/topics/${google_pubsub_topic.gcs_auto_remediate_topic.name}"
  filter           = var.org_sink_filter
  include_children = true
}

## Org level custom Cloud IAM role
resource "google_organization_iam_custom_role" "gcs_auto_remediate_custom_role" {
  role_id     = "gcs_auto_remediate_custom_role"
  org_id      = var.org_id
  title       = "GCS Auto Remediate Role"
  description = "Minimally privileged role to manage GCS buckets."
  permissions = var.function_perms
}

## Org level Cloud IAM member binding
resource "google_organization_iam_member" "gcs_auto_remediate_custom_role_member" {
  org_id = var.org_id
  role   = "organizations/${var.org_id}/roles/${google_organization_iam_custom_role.gcs_auto_remediate_custom_role.role_id}"
  member = "serviceAccount:${google_service_account.gcs_auto_remediate_cfn_sa.email}"
}

#############################
## Project level resources ##
#############################

## GCS Remediate Cloud Function Service Account
resource "google_service_account" "gcs_auto_remediate_cfn_sa" {
  account_id   = "${lower(var.name)}-gcs-auto-remediate-sa"
  display_name = "${var.name} GCS Auto Remediate CFN SA"
}

## Pub/Sub Topic for log exports
resource "google_pubsub_topic" "gcs_auto_remediate_topic" {
  name    = "${lower(var.name)}-gcs_auto_remediate_topic"
  project = var.project
}

## Log sink Cloud IAM binding
resource "google_pubsub_topic_iam_member" "publisher" {
  project = var.project
  topic   = google_pubsub_topic.gcs_auto_remediate_topic.name
  role    = "roles/pubsub.publisher"
  member  = google_logging_organization_sink.gcs_auto_remediate_sink.writer_identity
}

## Cloud Function source file
data "archive_file" "source" {
  type        = "zip"
  source_dir  = "../../src/public_gcs_bucket"
  output_path = "../../builds/public_gcs_bucket/public_gcs_bucket.zip"
}

## Cloud Function source bucket
resource "google_storage_bucket" "gcs_auto_remediate_cfn_bucket" {
  project = var.project
  name    = "${lower(var.name)}-gcs_auto_remediate_cfn_bucket_${var.project}"
}

## Cloud Function source file upload
resource "google_storage_bucket_object" "gcs_auto_remediate_cfn_source_archive" {
  name   = "src-${lower(replace(base64encode(data.archive_file.source.output_md5), "=", ""))}.zip"
  bucket = google_storage_bucket.gcs_auto_remediate_cfn_bucket.name
  source = data.archive_file.source.output_path
}

## GCS Remediate Cloud Function
resource "google_cloudfunctions_function" "iam_anomalous_grant_function" {
  name                  = local.function_name
  description           = "Cloud Function to remediate public GCS buckets."
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.gcs_auto_remediate_cfn_bucket.name
  source_archive_object = google_storage_bucket_object.gcs_auto_remediate_cfn_source_archive.name
  timeout               = 60
  entry_point           = "process_log_entry"
  service_account_email = google_service_account.gcs_auto_remediate_cfn_sa.email
  runtime               = "python38"

  event_trigger {
    event_type = "google.pubsub.topic.publish"
    resource   = google_pubsub_topic.gcs_auto_remediate_topic.name
  }
}
##################
# Example config
##################

# enabled_modules = {
#   public_bigquery_dataset = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "bqdataset",
#     log_sink_filter = "resource.type=\"bigquery_resource\"  protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get", "pubsub.topics.publish"],
#   }
#   public_gcs_bucket = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "gcs",
#     log_sink_filter = "resource.type=\"gcs_bucket\"  protoPayload.methodName=\"storage.setIamPermissions\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "storage.buckets.getIamPolicy", "storage.buckets.setIamPolicy", "pubsub.topics.publish"],
#   }
#   public_bigquery_table = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "bqtable",
#     log_sink_filter = "resource.type=\"bigquery_resource\" protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" protoPayload.resourceName=~\"tables/*\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.tables.setIamPolicy", "bigquery.tables.getIamPolicy", "pubsub.topics.publish", "bigquery.tables.get"],
#   }
#   public_compute_image = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "computeimage",
#     log_sink_filter = "resource.type=\"gce_image\" protoPayload.methodName=\"v1.compute.images.setIamPolicy\" protoPayload.request.policy.bindings.members=\"allAuthenticatedUsers\" OR protoPayload.request.policy.bindings.members=\"allUsers\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "compute.images.setIamPolicy", "compute.images.getIamPolicy", "pubsub.topics.publish"]
#   }
#   weak_ssl_policy = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "weakssl",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" protoPayload.request.minTlsVersion=\"TLS_1_0\" protoPayload.methodName=\"v1.compute.sslPolicies.patch\" OR protoPayload.methodName=\"v1.compute.sslPolicies.insert\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.sslPolicies.update", "compute.sslPolicies.get"],
#   }
#   compute_default_sa = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "gcedefaultsa",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" protoPayload.methodName=\"beta.compute.instances.insert\" protoPayload.methodName=\"v1.compute.instances.start\" protoPayload.request.serviceAccounts.email=~\"^\\d{1,12}-compute@developer.gserviceaccount.com$\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.instances.get", "compute.instances.stop"],
#   }
# }

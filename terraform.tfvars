##################
# Example config
##################


# project_id = "project123"

# enabled_modules = {
#   public_bigquery_dataset = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "bqdataset",
#     log_sink_filter = "resource.type=\"bigquery_dataset\"  protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get", "pubsub.topics.publish"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   public_gcs_bucket = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "gcs",
#     log_sink_filter = "resource.type=\"gcs_bucket\"  protoPayload.methodName=\"storage.setIamPermissions\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "storage.buckets.getIamPolicy", "storage.buckets.setIamPolicy", "pubsub.topics.publish"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   public_bigquery_table = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "bqtable",
#     log_sink_filter = "resource.type=\"bigquery_resource\" protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" protoPayload.resourceName=~\"tables/*\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.tables.setIamPolicy", "bigquery.tables.getIamPolicy", "pubsub.topics.publish", "bigquery.tables.get"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   public_compute_image = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "computeimage",
#     log_sink_filter = "resource.type=\"gce_image\" protoPayload.methodName=\"v1.compute.images.setIamPolicy\" AND (protoPayload.request.policy.bindings.members=\"allAuthenticatedUsers\" OR protoPayload.request.policy.bindings.members=\"allUsers\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "compute.images.setIamPolicy", "compute.images.getIamPolicy", "pubsub.topics.publish"]
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   weak_ssl_policy = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "weakssl",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" protoPayload.request.minTlsVersion=\"TLS_1_0\" AND (protoPayload.methodName=\"v1.compute.sslPolicies.patch\" OR protoPayload.methodName=\"v1.compute.sslPolicies.insert\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.sslPolicies.update", "compute.sslPolicies.get"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   compute_default_sa = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "gcedefaultsa",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" AND ((protoPayload.methodName=\"beta.compute.instances.insert\" AND protoPayload.request.serviceAccounts.email=~\"^\\d{1,12}-compute@developer.gserviceaccount.com$\") OR protoPayload.methodName=\"v1.compute.instances.start\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.instances.get", "compute.instances.stop"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
#   legacy_gke_abac = {
#     org_id = "123456",
#     project = "test_project",
#     region = "us-east1",
#     mode   = "read",
#     name = "gkeabac",
#     log_sink_filter = "(protoPayload.methodName=\"google.container.v1beta1.ClusterManager.CreateCluster\" AND operation.first=\"true\") OR (protoPayload.methodName=\"google.container.v1.ClusterManager.SetLegacyAbac\" AND protoPayload.request.enabled=\"true\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "container.clusters.get", "container.clusters.update"],
#     allowlist = ["example-projectid-1", "example-projectid-2"],
#   }
# }

##################
# Example config
##################


# alert_topic_project_id = "security_project"
# org_id                 = "1234567890"
# mode                   = "read"
# project_list           = "project123,projectabc"
# list_type              = "allow"
# region                 = "us-east1"

# enabled_modules = {
#   public_bigquery_dataset = {
#     lockdown_project = "test_project",
#     name = "bqdataset",
#     log_sink_filter = "resource.type=\"bigquery_dataset\"  protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get", "pubsub.topics.publish"],
#   }
#   public_gcs_bucket = {
#     lockdown_project = "test_project",
#     name = "gcs",
#     log_sink_filter = "resource.type=\"gcs_bucket\"  protoPayload.methodName=\"storage.setIamPermissions\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "storage.buckets.getIamPolicy", "storage.buckets.setIamPolicy", "pubsub.topics.publish"],
#   }
#   public_bigquery_table = {
#     lockdown_project = "test_project",
#     name = "bqtable",
#     log_sink_filter = "resource.type=\"bigquery_resource\" protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" protoPayload.resourceName=~\"tables/*\" AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "bigquery.tables.setIamPolicy", "bigquery.tables.getIamPolicy", "pubsub.topics.publish", "bigquery.tables.get"],
#   }
#   public_compute_image = {
#     lockdown_project = "test_project",
#     name = "computeimage",
#     log_sink_filter = "resource.type=\"gce_image\" protoPayload.methodName=\"v1.compute.images.setIamPolicy\" AND (protoPayload.request.policy.bindings.members=\"allAuthenticatedUsers\" OR protoPayload.request.policy.bindings.members=\"allUsers\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "compute.images.setIamPolicy", "compute.images.getIamPolicy", "pubsub.topics.publish"]
#   }
#   weak_ssl_policy = {
#     lockdown_project = "test_project",
#     name = "weakssl",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" protoPayload.request.minTlsVersion=\"TLS_1_0\" AND (protoPayload.methodName=\"v1.compute.sslPolicies.patch\" OR protoPayload.methodName=\"v1.compute.sslPolicies.insert\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.sslPolicies.update", "compute.sslPolicies.get"],
#   }
#   compute_default_sa = {
#     lockdown_project = "test_project",
#     name = "gcedefaultsa",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" AND ((protoPayload.methodName=\"beta.compute.instances.insert\" AND protoPayload.request.serviceAccounts.email=~\"^\\d{1,12}-compute@developer.gserviceaccount.com$\") OR protoPayload.methodName=\"v1.compute.instances.start\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "compute.instances.get", "compute.instances.stop"],
#   }
#   legacy_gke_abac = {
#     lockdown_project = "test_project",
#     name = "gkeabac",
#     log_sink_filter = "(protoPayload.methodName=\"google.container.v1beta1.ClusterManager.CreateCluster\" AND operation.first=\"true\") OR (protoPayload.methodName=\"google.container.v1.ClusterManager.SetLegacyAbac\" AND protoPayload.request.enabled=\"true\") AND NOT protoPayload.authenticationInfo.principalEmail"
#     function_perms = ["logging.logEntries.create", "pubsub.topics.publish", "container.clusters.get", "container.clusters.update"],
#   }
#   public_firewall_port = {
#     lockdown_project = "test_project",
#     name   = "fwrule",
#     function_memory = 256,
#     log_sink_filter = "resource.type=\"gce_firewall_rule\" AND (protoPayload.methodName=\"v1.compute.firewalls.insert\" OR protoPayload.methodName=\"v1.compute.firewalls.update\" OR protoPayload.methodName=\"v1.compute.firewalls.patch\") AND NOT protoPayload.request.disabled=true AND operation.last=true AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "compute.firewalls.get", "compute.firewalls.update", "compute.networks.updatePolicy"],
#   }
# }

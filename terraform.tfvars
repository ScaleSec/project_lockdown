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
#     name = "gcedefsa",
#     log_sink_filter = "protoPayload.serviceName=\"compute.googleapis.com\" AND ((protoPayload.methodName=\"beta.compute.instances.insert\" AND protoPayload.request.serviceAccounts.email=~\"^\\d{1,18}-compute@developer.gserviceaccount.com$\") OR protoPayload.methodName=\"v1.compute.instances.start\") AND NOT protoPayload.authenticationInfo.principalEmail"
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
#   public_pubsub_topic = {
#     lockdown_project = "test_project",
#     name   = "publictopic",
#     log_sink_filter = "resource.type=\"pubsub_topic\" AND protoPayload.methodName=\"google.iam.v1.IAMPolicy.SetIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "pubsub.topics.setIamPolicy", "pubsub.topics.getIamPolicy"],
#   }
#   kms_key_rotation = {
#     lockdown_project = "test_project",
#     name   = "kmsrotation",
#     log_sink_filter  = "protoPayload.serviceName=\"cloudkms.googleapis.com\" AND (protoPayload.methodName=\"CreateCryptoKey\" OR (protoPayload.methodName=\"UpdateCryptoKey\" AND protoPayload.request.updateMask=~\"rotationPeriod\")) AND resource.type=\"cloudkms_cryptokey\" AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "cloudkms.cryptoKeys.get", "cloudkms.cryptoKeys.update"],
#   }
#   public_kms_keys = {
#     lockdown_project = "test_project",
#     name   = "publickms",
#     log_sink_filter = "protoPayload.serviceName=\"cloudkms.googleapis.com\" AND protoPayload.methodName=\"SetIamPolicy\" AND (resource.type=\"cloudkms_cryptokey\" OR resource.type=\"cloudkms_keyring\") AND (protoPayload.request.policy.bindings.members=\"allAuthenticatedUsers\" OR protoPayload.request.policy.bindings.members=\"allUsers\") AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "cloudkms.cryptoKeys.getIamPolicy", "cloudkms.cryptoKeys.setIamPolicy", "cloudkms.keyRings.getIamPolicy", "cloudkms.keyRings.setIamPolicy"],
#   }
#   public_artifact_repo = {
#     lockdown_project = "test_project",
#     name   = "publicrepo",
#     log_sink_filter = "protoPayload.serviceName=\"artifactregistry.googleapis.com\" protoPayload.request.@type=\"type.googleapis.com/google.iam.v1.SetIamPolicyRequest\" protoPayload.authorizationInfo.permission=\"artifactregistry.repositories.setIamPolicy\" AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "artifactregistry.repositories.getIamPolicy", "artifactregistry.repositories.setIamPolicy"],
#   }
#   protect_lockdown_sa = {
#     lockdown_project = "test_project",
#     name   = "protectlockdownsa",
#     log_sink_filter = "resource.labels.email_id=~\"^[a-z-]{1,21}-lockdown@*\" AND protoPayload.methodName=\"google.iam.admin.v1.SetIAMPolicy\" AND (protoPayload.serviceData.policyDelta.bindingDeltas.role=\"aiplatform.customCodeServiceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"aiplatform.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"appengineflex.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"bigquerydatatransfer.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"cloudbuild.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"clouddeploy.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"cloudfunctions.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"cloudscheduler.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"cloudtasks.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"cloudtpu.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"composer.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"compute.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"container.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"dataflow.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"dataprep.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"dataproc.hubAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"dataproc.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"editor\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"eventarc.serviceAgent\"OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"genomics.serviceAgent\"\ OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"iam.serviceAccountKeyAdmin" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"iam.serviceAccountTokenCreator\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"iam.serviceAccountUser\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"iam.workloadIdentityUser\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"lifesciences.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"ml.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"notebooks.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"osconfig.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"owner\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"pubsub.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"run.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"serverless.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"sourcerepo.serviceAgent\" OR protoPayload.serviceData.policyDelta.bindingDeltas.role=\"workflows.serviceAgent\") AND NOT protoPayload.authenticationInfo.principalEmail",
#     function_perms  = ["logging.logEntries.create", "pubsub.topics.publish", "iam.serviceAccounts.getIamPolicy", "iam.serviceAccounts.setIamPolicy"],
#   }
# }

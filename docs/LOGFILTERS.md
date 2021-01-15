# Cloud Logging (formally Stackdriver) Log Filters

Cloud Logging supports a feature called [Advanced logs queries](https://cloud.google.com/logging/docs/view/advanced-queries) where you are able to use query expressions to select unique log entries. Project Lockdown leverages advanced log queries in order to only invocate for very specific scenarios where a remediation may be needed. To get started with advanced log queries, visit the documentation [here](https://cloud.google.com/logging/docs/view/advanced-queries#getting-started).

## Project Lockdown Log Sink Filters

The following table contains the log sink filters (advanced log queries) used by Project Lockdown. Input any of the below log queries into the Cloud Logging console (steps above) to view which events will be sent to Project Lockdown. 

| Product/Service | Advanced log query | 
|-----------------|--------------------|
| GCE Service Accounts | `protoPayload.serviceName="compute.googleapis.com" AND ((protoPayload.methodName="beta.compute.instances.insert" AND protoPayload.request.serviceAccounts.email=~"^\\d{1,12}-compute@developer.gserviceaccount.com$") OR protoPayload.methodName="v1.compute.instances.start")`
| GCE Images | `resource.type="gce_image" protoPayload.methodName="v1.compute.images.setIamPolicy" AND (protoPayload.request.policy.bindings.members="allAuthenticatedUsers" OR protoPayload.request.policy.bindings.members="allUsers")`
| SSL Policies | `protoPayload.serviceName="compute.googleapis.com" protoPayload.request.minTlsVersion="TLS_1_0" AND (protoPayload.methodName="v1.compute.sslPolicies.patch" OR protoPayload.methodName="v1.compute.sslPolicies.insert")`
| GKE ABAC | `protoPayload.methodName="google.container.v1beta1.ClusterManager.CreateCluster" AND operation.first="true") OR (protoPayload.methodName="google.container.v1.ClusterManager.SetLegacyAbac" AND protoPayload.request.enabled="true")`
| BigQuery Datasets | `resource.type="bigquery_dataset" protoPayload.methodName="google.iam.v1.IAMPolicy.SetIamPolicy"`
| BigQuery Tables | `resource.type="bigquery_resource" protoPayload.methodName="google.iam.v1.IAMPolicy.SetIamPolicy" protoPayload.resourceName=~"tables/*"`
| GCS Buckets| `resource.type="gcs_bucket"  protoPayload.methodName="storage.setIamPermissions"`
| Firewall Rules | `resource.type="gce_firewall_rule" AND (protoPayload.methodName="v1.compute.firewalls.insert" OR protoPayload.methodName="v1.compute.firewalls.update" OR protoPayload.methodName="v1.compute.firewalls.patch") AND NOT protoPayload.request.disabled=true AND operation.last=true`
| Pub/Sub Topics | `resource.type="pubsub_topic" AND protoPayload.methodName="google.iam.v1.IAMPolicy.SetIamPolicy"`


__Note:__ The above queries have been modified to work in the GCP console from their terraform configuration. In terraform we add an extra parameter to not invocate when Project Lockdown performs an action. Without that additional config, Project Lockdown would invocate itself causing additional costs. To view the terraform log sink filters view the example `tfvars` file [here](../terraform.tfvars).
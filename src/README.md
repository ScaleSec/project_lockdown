# Project Lockdown Automated Remediation Scenarios
All lockdown remediation functions are triggered via a Pub/Sub push message based on a specific log sink query. You can find examples in the [documentation](../docs/LOGFILTERS.md). Keep in mind that by default Project Lockdown deploys in read only. You will need to update the `mode` variable in your [terraform.tfvars](../terraform.tfvars) file to be "write" in order to turn on automate remediations.

## Deny use of the default compute service account on GCE Instances
- The use of the [default compute service account](https://cloud.google.com/compute/docs/access/service-accounts#default_service_account) on GCE instances is a potentially large security risk due to the IAM role `roles/editor` being applied to the SA. Typically this IAM role is overly permissive for workloads in GCE and should be avoided. A best practice is to avoid all [basic IAM roles](https://cloud.google.com/iam/docs/understanding-roles#basic) (previously called primitive roles) and instead create custom least privilege roles.
- This remediation function will monitor for create and start events for GCE instances in Cloud Logging and analyze the assigned service account. If the GCE instance is using the default compute service account the function will stop the instance and log the finding to Pub/Sub.

## Update weak TLS 1.0 to 1.1 on SSL Policies
- TLS 1.0 is generally deprecated across many enterprise devices and is considered a weak encryption protocol. While some legacy applications still require TLS 1.0, we typically recommend customers migrate to at least TLS 1.1 but preferably 1.2.
- This remediation will monitor for create and update events in Cloud Logging for SSL policies. If the SSL policy is using TLS 1.0, the function will update the policy to use TLS 1.1 and log the finding to Pub/Sub.

## Disable Legacy auth (ABAC) on GKE clusters
- Legacy authentication for GKE is considered unsecure and should be avoided. Organizations interested in using GKE should either use role-based authentication (RBAC) or GKE's [Workload Identity](https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity). If a cluster is created with ABAC enabled or if a cluster is updated to enable ABAC, Project Lockdown will attempt to disable that setting for 5 minutes. If the 5 minute timeout is eclipsed, the function will gracefully timeout. 

## Publicly Exposed Resources
- Publicly exposed resources pose one of the largest attack targets in the cloud. Malicious actors are constantly scanning for public resources in order to exfiltrate customer data, gain access to customer's environments, or even sabotage with an aim to disrupt workloads. With this in mind, the main bulk of our first remediations are around keeping your resources private. We try to target scenarios where there are no current safeguards available from GCP (Organization Policy constraints, for example.)

### Remove Public IAM bindings from BigQuery datasets
- This remediation will monitor for IAM policy updates on BigQuery datasets and search for the public `allUsers` and `allAuthenticatedUsers` IAM bindings. If either of those are currently assigned to the dataset, the function will remove the binding(s) and log the finding to Pub/Sub.

### Remove Public IAM bindings from BigQuery Tables
- This remediation will monitor for IAM policy updates on BigQuery tables and search for the public `allUsers` and `allAuthenticatedUsers` IAM bindings. If either of those are currently assigned to the table, the function will remove the binding(s) and log the finding to Pub/Sub.

### Remove Public IAM bindings from GCE Images
- This remediation will monitor for IAM policy updates on GCE images and search for the public `allAuthenticatedUsers` IAM binding (`allUsers` is not supported on this resource type but we still look for it in the Cloud Logging query). If a public IAM member is currently assigned to the GCE image, the function will remove the binding and log the finding to Pub/Sub.

### Remove Public IAM bindings from GCS Buckets
- This remediation will monitor for IAM policy updates on GCS buckets and search for the public `allUsers` and `allAuthenticatedUsers` IAM bindings. If a public IAM member is currently assigned to the GCS bucket, the function will remove the binding(s) and log the finding to Pub/Sub.

### Disable Firewalls with 0.0.0.0/0 ingress source ranges
- This remediation will monitor for updates to existing firewalls and creation of new firewalls. It will check for 0.0.0.0/0 in source ranges of the firewall, and if it does exist, disable the firewall and log the finding to Pub/Sub.

### Remove Public IAM bindings from Pub/Sub Topics
- This remediation will monitor for IAM policy updates on Pub/Sub Topics and search for the public `allUsers` and `allAuthenticatedUsers` IAM bindings. If a public IAM member is currently assigned to the topic, the function will remove the binding(s) and log the finding to Pub/Sub.

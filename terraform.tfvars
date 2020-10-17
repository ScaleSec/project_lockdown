enabled_modules = {
  public_bigquery_dataset = {
    org_id = "123456",
    project = "test_project",
    region = "us-east1",
    name = "bigquery",
    function_perms = ["logging.logEntries.create", "bigquery.datasets.update", "bigquery.datasets.get"],
  }
  public_gcs_bucket = {
    org_id = "123456",
    project = "test_project",
    region = "us-east1",
    name = "gcs",
    function_perms = ["logging.logEntries.create", "storage.buckets.getIamPolicy", "storage.buckets.setIamPolicy"],
  }

}
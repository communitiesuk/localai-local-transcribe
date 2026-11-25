locals {
  # Council audio is uploaded to quarantine. Once scanned and found clean it is copied to
  # assets. Outputs holds what each run produces, and results holds aggregated metrics.
  evals_bucket_names = toset(["quarantine", "assets", "outputs", "results"])
}

# The shared bucket module blocks public access, requires TLS, turns on versioning and writes
# access logs to a second bucket. Old versions of data objects are kept for 14 days, which
# matches the product uploads bucket. Deleting an object therefore removes it for good after
# 14 days. The access log buckets keep their old versions for 365 days.
# No bucket is public. Council uploads use a presigned URL, which works with public access
# blocked because it carries the signer's permissions.
module "evals_bucket" {
  for_each = local.evals_bucket_names
  source   = "../s3_bucket"

  bucket_name            = "${var.environment_name}-local-transcribe-evals-${each.key}"
  access_log_bucket_name = "${var.environment_name}-local-transcribe-evals-${each.key}-log"
  kms_key_arn            = aws_kms_key.evals.arn

  noncurrent_version_expiration_days            = 14
  log_bucket_noncurrent_version_expiration_days = 365
}

locals {
  # Council audio is uploaded to quarantine. Once scanned and found clean it is copied to
  # assets. Outputs holds what each run produces, and results holds aggregated metrics.
  evals_bucket_names = toset(["quarantine", "assets", "outputs", "results"])
}

# The shared bucket module blocks public access, requires TLS, turns on versioning and writes
# access logs to a second bucket. Old versions and logs are kept for its default of 365 days.
# No bucket is public. Council uploads use a presigned URL, which works with public access
# blocked because it carries the signer's permissions.
module "evals_bucket" {
  for_each = local.evals_bucket_names
  source   = "../s3_bucket"

  bucket_name            = "${var.environment_name}-local-transcribe-evals-${each.key}"
  access_log_bucket_name = "${var.environment_name}-local-transcribe-evals-${each.key}-log"
  kms_key_arn            = aws_kms_key.evals.arn
}

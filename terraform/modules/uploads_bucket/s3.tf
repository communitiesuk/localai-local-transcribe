module "uploads_bucket" {
  source = "../s3_bucket"

  bucket_name = "${var.environment_name}-local-transcribe-uploads"
  access_log_bucket_name = "${var.environment_name}-local-transcribe-uploads-log"
  access_s3_log_expiration_days = var.access_s3_log_expiration_days
  force_destroy = var.force_destroy
  kms_key_arn = var.kms_key
}
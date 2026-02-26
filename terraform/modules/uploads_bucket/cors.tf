resource "aws_s3_bucket_cors_configuration" "cors" {
  bucket = module.uploads_bucket.bucket_id

  expected_bucket_owner = data.aws_caller_identity.current.account_id #deprecated field

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "GET", "POST"]
    allowed_origins = ["https://${var.app_host}", "http://localhost:3000"]
    max_age_seconds = 3000
  }
}


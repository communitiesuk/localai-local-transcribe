resource "aws_s3_bucket" "minute_bucket" {
  # checkov:skip=CKV_AWS_144:No need for cross region replication
  # checkov:skip=CKV2_AWS_61:Disable need for lifecycle configuration
  # checkov:skip=CKV2_AWS_62:Disable event notifications enabled
  bucket        = "${var.environment_name}-minute-data"
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_versioning" "minute_bucket" {
  bucket = aws_s3_bucket.minute_bucket.id
  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "minute_bucket" {
  # checkov:skip=CKV2_AWS_67:Ensure AWS S3 bucket encrypted with Customer Managed Key (CMK) has regular rotation
  bucket = aws_s3_bucket.minute_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_policy" "minute_bucket" {
  bucket = aws_s3_bucket.minute_bucket.id
  policy = data.aws_iam_policy_document.app_bucket.json
}

resource "aws_s3_bucket_public_access_block" "minute_bucket" {
  bucket = aws_s3_bucket.minute_bucket.id

  ignore_public_acls      = true
  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "log_bucket" {
  # checkov:skip=CKV_AWS_144:No need for cross region replication
  # checkov:skip=CKV2_AWS_61:Disable need for lifecycle configuration
  # checkov:skip=CKV2_AWS_62:Disable event notifications enabled
  bucket        = "${var.environment_name}-minute-logs-bucket"
  force_destroy = var.force_destroy
}

resource "aws_s3_bucket_logging" "minute_bucket" {
  bucket        = aws_s3_bucket.minute_bucket.id
  target_bucket = aws_s3_bucket.log_bucket.id
  target_prefix = "log/"
}

resource "aws_s3_bucket_server_side_encryption_configuration" "log_bucket" {
  # checkov:skip=CKV2_AWS_67:Ensure AWS S3 bucket encrypted with Customer Managed Key (CMK) has regular rotation
  bucket = aws_s3_bucket.log_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id

  rule {
    id = "expire-old-logs"

    filter {}

    expiration {
      days = var.access_s3_log_expiration_days
    }

    status = "Enabled"
  }
}

resource "aws_s3_bucket_policy" "allow_log_writes" {
  bucket = aws_s3_bucket.log_bucket.id
  policy = data.aws_iam_policy_document.allow_log_writes.json
}

resource "aws_s3_bucket_public_access_block" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id

  ignore_public_acls      = true
  block_public_acls       = true
  block_public_policy     = true
  restrict_public_buckets = true
}

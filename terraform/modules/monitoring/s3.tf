module "s3_bucket" {
  source = "../s3_bucket"

  access_log_bucket_name             = "prsdb-cloudtrail-${var.environment_name}-access-logs"
  bucket_name                        = "prsdb-cloudtrail-${var.environment_name}"
  access_s3_log_expiration_days      = var.cloudwatch_log_expiration_days
  policy                             = data.aws_iam_policy_document.bucket_policy.json
  kms_key_arn                        = aws_kms_key.main.arn
  noncurrent_version_expiration_days = null
}

resource "aws_s3_bucket_lifecycle_configuration" "expire" {
  bucket = module.s3_bucket.bucket

  rule {
    id = "expiration"
    filter {
      prefix = ""
    }
    expiration {
      days = var.cloudwatch_log_expiration_days
    }

    noncurrent_version_expiration {
      noncurrent_days = var.cloudwatch_log_expiration_days
    }

    status = "Enabled"
  }
}

data "aws_iam_policy_document" "bucket_policy" {
  statement {
    sid    = "AWSCloudTrailAclCheck"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions   = ["s3:GetBucketAcl"]
    resources = [module.s3_bucket.bucket_arn]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/prsd-cloudtrail-${var.environment_name}"
      ]
    }
  }

  statement {
    sid    = "AWSCloudTrailWrite"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions   = ["s3:PutObject"]
    resources = ["${module.s3_bucket.bucket_arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values = [
        "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/prsd-cloudtrail-${var.environment_name}"
      ]
    }
  }
}
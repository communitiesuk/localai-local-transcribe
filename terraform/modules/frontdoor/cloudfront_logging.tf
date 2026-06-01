data "aws_caller_identity" "current" {}

resource "aws_s3_bucket" "cloudfront_logs" {
  bucket              = "cloudfront-logs--${data.aws_caller_identity.current.account_id}-${var.environment_name}"
  force_destroy       = false
  object_lock_enabled = false
}

resource "aws_s3_bucket_versioning" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_cloudwatch_log_delivery_source" "cloudfront_logs" {
  name         = "${var.environment_name}-cloudfront-logs-source"
  log_type     = "ACCESS_LOGS"
  resource_arn = aws_cloudfront_distribution.main.arn
  provider     = aws.us-east-1
}

resource "aws_cloudwatch_log_delivery_destination" "cloudfront_logs" {
  name                      = "${var.environment_name}-cloudfront-logs-destination"
  delivery_destination_type = "S3"
  delivery_destination_configuration {
    destination_resource_arn = aws_s3_bucket.cloudfront_logs.arn

  }
  output_format = "json"
  provider      = aws.us-east-1

}

resource "aws_cloudwatch_log_delivery" "cloudfront_logs" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.cloudfront_logs.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.cloudfront_logs.arn
  provider                 = aws.us-east-1
  depends_on               = [aws_s3_bucket_policy.cloudfront_logs]
}


resource "aws_s3_bucket_policy" "cloudfront_logs" {
  bucket     = aws_s3_bucket.cloudfront_logs.id
  policy     = data.aws_iam_policy_document.allow_cloudfront_log_writes.json
  depends_on = [aws_cloudwatch_log_delivery_destination.cloudfront_logs]
}


data "aws_iam_policy_document" "allow_cloudfront_log_writes" {
  statement {
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions = ["s3:PutObject", "s3:PutObjectAcl", "s3:AbortMultipartUpload", "s3:ListBucket"]

    resources = ["${aws_s3_bucket.cloudfront_logs.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values = [
        aws_cloudwatch_log_delivery_destination.cloudfront_logs.arn
      ]
    }
  }

  statement {
    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions = ["s3:GetBucketAcl"]

    resources = [
      aws_s3_bucket.cloudfront_logs.arn
    ]
  }

  statement {
    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    effect = "Deny"

    resources = [
      aws_s3_bucket.cloudfront_logs.arn,
      "${aws_s3_bucket.cloudfront_logs.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}


resource "aws_s3_bucket_public_access_block" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_kms_key" "cloudfront_logs" {
  description         = "local-transcribe-cloudfront-logs-${var.environment_name}"
  enable_key_rotation = true
}

resource "aws_kms_alias" "cloudfront_logs" {
  name          = "alias/${var.environment_name}-cloudfront-logs"
  target_key_id = aws_kms_key.cloudfront_logs.key_id
}

resource "aws_kms_key_policy" "cloudfront_logs" {
  key_id = aws_kms_key.cloudfront_logs.id
  policy = data.aws_iam_policy_document.cloudfront_logs_kms.json
}




data "aws_iam_policy_document" "cloudfront_logs_kms" {
  statement {
    sid = "AllowRootAccountAccess"

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = [aws_kms_key.cloudfront_logs.arn]
  }

  statement {
    sid = "AllowCloudFrontLogDelivery"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions = [
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
      "kms:Encrypt*",
    ]

    resources = [aws_kms_key.cloudfront_logs.arn]
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudfront_logs" {
  bucket = aws_s3_bucket.cloudfront_logs.bucket

  rule {
    bucket_key_enabled = true

    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.cloudfront_logs.arn
    }
  }
}


resource "aws_s3_bucket_lifecycle_configuration" "cloudfront_logs" {
  bucket     = aws_s3_bucket.cloudfront_logs.id
  depends_on = [aws_s3_bucket_versioning.cloudfront_logs]

  rule {
    id = "expire-old-logs"
    filter {}

    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }


    expiration {
      days = 365
    }

  }

}
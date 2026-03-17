module "quarantine_bucket" {
  source                             = "../s3_bucket"
  bucket_name                        = "prsdb-quarantine-${var.environment_name}"
  access_log_bucket_name             = "prsdb-quarantine-access-logs-${var.environment_name}"
  noncurrent_version_expiration_days = 700
  access_s3_log_expiration_days      = 700
  kms_key_arn                        = aws_kms_key.quarantine_bucket_encryption_key.arn
}

resource "aws_kms_key" "quarantine_bucket_encryption_key" {
  description         = "Quarantine bucket encryption key"
  enable_key_rotation = true
}

resource "aws_kms_alias" "quarantine_bucket_encryption_key" {
  name          = "alias/quarantine-encryption-${var.environment_name}"
  target_key_id = aws_kms_key.quarantine_bucket_encryption_key.key_id
}

# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "upload_to_quarantine" {
  statement {
    sid = "QuarantineS3"
    actions = [
      "s3:PutObject",
      "s3:GetObject",
      "s3:GetObjectTagging",
      "s3:DeleteObject",
    ]
    resources = [
      "${module.quarantine_bucket.bucket_arn}/*",
    ]
  }

  statement {
    sid    = "AllowKMSUsage"
    effect = "Allow"
    actions = [
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:Decrypt",
    ]
    resources = [
      aws_kms_key.quarantine_bucket_encryption_key.arn
    ]
  }
}

resource "aws_iam_policy" "upload_to_quarantine" {
  name   = "upload-to-quarantine"
  policy = data.aws_iam_policy_document.upload_to_quarantine.json
}

resource "aws_iam_role_policy_attachment" "ecs_quarantine_s3_attachment" {
  role       = var.webapp_task_execution_role_name
  policy_arn = aws_iam_policy.upload_to_quarantine.arn
}
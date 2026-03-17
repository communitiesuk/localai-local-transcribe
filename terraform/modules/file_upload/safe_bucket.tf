module "uploaded_files_bucket" {
  source                             = "../s3_bucket"
  bucket_name                        = "prsdb-uploaded-files-${var.environment_name}"
  access_log_bucket_name             = "prsdb-uploaded-files-access-logs-${var.environment_name}"
  noncurrent_version_expiration_days = 700
  access_s3_log_expiration_days      = 700
  kms_key_arn                        = aws_kms_key.uploaded_files_bucket_encryption_key.arn
}

resource "aws_kms_key" "uploaded_files_bucket_encryption_key" {
  description         = "Safe bucket encryption key"
  enable_key_rotation = true
}

resource "aws_kms_alias" "uploaded_files_bucket_encryption_key" {
  name          = "alias/uploaded-files-encryption-${var.environment_name}"
  target_key_id = aws_kms_key.uploaded_files_bucket_encryption_key.key_id
}

# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "upload_to_safe" {
  statement {
    sid = "SafeS3"
    actions = [
      "s3:PutObject",
      "s3:PutObjectTagging",
    ]
    resources = [
      "${module.uploaded_files_bucket.bucket_arn}/*",
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
      aws_kms_key.uploaded_files_bucket_encryption_key.arn
    ]
  }
}


# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "download_from_safe" {
  statement {
    sid = "DownloadFromSafeS3"
    actions = [
      "s3:GetObject",
      "s3:GetObjectVersion",
    ]
    resources = [
      "${module.uploaded_files_bucket.bucket_arn}/*",
    ]
  }

  statement {
    sid    = "AllowKMSUsage"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
    ]
    resources = [
      aws_kms_key.uploaded_files_bucket_encryption_key.arn
    ]
  }
}

resource "aws_iam_policy" "download_from_safe" {
  name   = "download-from-safe"
  policy = data.aws_iam_policy_document.download_from_safe.json
}

resource "aws_iam_role_policy_attachment" "ecs_download_files_from_s3_attachment" {
  role       = var.webapp_task_execution_role_name
  policy_arn = aws_iam_policy.download_from_safe.arn
}

resource "aws_iam_policy" "upload_to_safe" {
  name   = "upload-to-safe"
  policy = data.aws_iam_policy_document.upload_to_safe.json
}

resource "aws_iam_role_policy_attachment" "ecs_uploaded_files_s3_attachment" {
  role       = var.webapp_task_execution_role_name
  policy_arn = aws_iam_policy.upload_to_safe.arn
}
terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
  }
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

resource "aws_kms_key" "state_bucket_encryption_key" {
  description         = "Terraform state bucket encryption key"
  enable_key_rotation = true
}

resource "aws_kms_alias" "state_bucket_encryption_key" {
  name          = "alias/terraform-state-encryption-${var.environment_name}"
  target_key_id = aws_kms_key.state_bucket_encryption_key.key_id
}

module "state_bucket" {
  source                             = "../s3_bucket"
  bucket_name                        = "local-transcribe-tfstate-${var.environment_name}"
  access_log_bucket_name             = "local-transcribe-tfstate-access-logs-${var.environment_name}"
  kms_key_arn                        = aws_kms_key.state_bucket_encryption_key.arn
  noncurrent_version_expiration_days = 700
  access_s3_log_expiration_days      = 700
}

# Access to Terraform state, should be enough to do a terraform plan along with ReadOnlyAccess
# tfsec:ignore:aws-iam-no-policy-wildcards
data "aws_iam_policy_document" "terraform_state_read_only" {
  statement {
    sid = "TFStateS3"
    actions = [
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      module.state_bucket.bucket_arn,
      "${module.state_bucket.bucket_arn}/*",
    ]
  }

  statement {
    sid = "TFStateKMSKey"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey",
    ]
    resources = [aws_kms_key.state_bucket_encryption_key.arn]
  }

  statement {
    sid = "ReadTFManagedSecrets"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      # Access secrets managed by Terraform
      "arn:aws:secretsmanager:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:secret:tf-*",
    ]
  }

  # Other secrets and keys Terraform needs to be able to read during plan
  statement {
    sid = "ReadPlanSecrets"
    actions = [
      "secretsmanager:GetSecretValue",
      "kms:Decrypt",
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:resourceTag/terraform-plan-read"
      values   = ["true"]
    }
  }

  statement {
    # Missing from ReadOnlyAccess
    sid       = "ListLogDeliveries"
    actions   = ["logs:ListLogDeliveries"]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "terraform_state_read_only" {
  name   = "tf-state-read-only"
  policy = data.aws_iam_policy_document.terraform_state_read_only.json
}

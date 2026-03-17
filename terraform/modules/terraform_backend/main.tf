terraform {
  required_version = "~>1.9.1"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.0"
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
  bucket_name                        = "prsdb-tfstate-${var.environment_name}"
  access_log_bucket_name             = "prsdb-tfstate-access-logs-${var.environment_name}"
  kms_key_arn                        = aws_kms_key.state_bucket_encryption_key.arn
  noncurrent_version_expiration_days = 700
  access_s3_log_expiration_days      = 700
}

# Encryption/recovery not required - lock not sensitive
# tfsec:ignore:aws-dynamodb-enable-at-rest-encryption tfsec:ignore:aws-dynamodb-enable-recovery tfsec:ignore:aws-dynamodb-table-customer-key
resource "aws_dynamodb_table" "terraform_state_lock" {
  name           = "tfstate-lock-${var.environment_name}"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
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
    sid = "TFStateLock"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = [aws_dynamodb_table.terraform_state_lock.arn]
  }

  statement {
    sid = "ReadTFManagedSecrets"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [
      # Access secrets managed by Terraform
      "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:tf-*",
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

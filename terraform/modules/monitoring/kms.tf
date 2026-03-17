resource "aws_kms_key" "main" {
  enable_key_rotation = true
  description         = "prsdb-cloudtrail-${var.environment_name}"
}

resource "aws_kms_key_policy" "main" {
  key_id = aws_kms_key.main.key_id
  policy = data.aws_iam_policy_document.cloudtrail_kms.json
}

resource "aws_kms_alias" "main" {
  name          = "alias/cloudtrail-${var.environment_name}"
  target_key_id = aws_kms_key.main.key_id
}

data "aws_iam_policy_document" "cloudtrail_kms" {
  statement {
    principals {
      type        = "Service"
      identifiers = ["logs.${data.aws_region.current.name}.amazonaws.com"]
    }

    actions = [
      "kms:Encrypt*",
      "kms:Decrypt*",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:Describe*"
    ]

    resources = ["*"]
    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${module.cloudtrail_cloudwatch_group.name}"]
    }
  }

  # Required to allow the KMS key to be managed after creation: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions = ["kms:*"]

    resources = [aws_kms_key.main.arn]
  }

  # This statement allows CloudTrail to use the KMS key for encryption
  statement {
    principals {
      type        = "Service"
      identifiers = ["cloudtrail.amazonaws.com"]
    }

    actions = ["kms:GenerateDataKey*"]


    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = ["arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:trail/prsd-cloudtrail-${var.environment_name}"]
    }
  }
}
data "aws_caller_identity" "current" {}

resource "aws_kms_key" "main" {
  description             = "local-transcribe-app-config-${var.environment_name}"
  enable_key_rotation     = true
  rotation_period_in_days = 180

  tags = {
    type        = "AppConfig KMS Key"
    Environment = "${var.environment_name}"
  }
}

resource "aws_kms_alias" "main" {
  name          = "alias/local-transcribe-app-config-${var.environment_name}"
  target_key_id = aws_kms_key.main.key_id
}

resource "aws_kms_key_policy" "main" {
  key_id = aws_kms_key.main.id
  policy = data.aws_iam_policy_document.app_config_kms.json
}

data "aws_iam_policy_document" "app_config_kms" {
  # Required to allow the KMS key to be managed after creation: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    effect = "Allow"

    actions = ["kms:*"]

    resources = [aws_kms_key.main.arn]
  }

  statement {
    principals {
      type        = "Service"
      identifiers = ["appconfig.amazonaws.com"]
    }

    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]

    resources = [aws_kms_key.main.arn]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

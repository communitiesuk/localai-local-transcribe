data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms_secrets_decrypt" {
  statement {
    principals {
      type        = "AWS"
      identifiers = [var.webapp_task_execution_role_arn]
    }

    actions = ["kms:Decrypt"]

    resources = [aws_kms_key.minute_webapp_secrets.arn]
  }

  # Required to allow the KMS key to be managed after creation: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions = ["kms:*"]

    resources = [aws_kms_key.minute_webapp_secrets.arn]
  }
}

resource "aws_kms_key_policy" "kms_webapp_secrets_decrypt_policy" {
  key_id = aws_kms_key.minute_webapp_secrets.key_id
  policy = data.aws_iam_policy_document.kms_secrets_decrypt.json
}

resource "aws_iam_role_policy" "secret_access" {
  name = "${var.environment_name}-secret-access"
  role = var.webapp_task_execution_role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Effect = "Allow"
        Resource = [
          aws_secretsmanager_secret.database_password.arn,
          aws_secretsmanager_secret.redis_password.arn,
          aws_secretsmanager_secret.one_login_private_key.arn,
          aws_secretsmanager_secret.notify_api_key.arn,
          aws_secretsmanager_secret.os_api_key.arn,
          aws_secretsmanager_secret.epc_register_client_secret.arn,
        ]
      }
    ]
  })
}
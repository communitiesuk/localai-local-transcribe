data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "kms_secrets_decrypt" {
  statement {
    principals {
      type        = "AWS"
      identifiers = [var.frontend_task_execution_role_arn, var.backend_task_execution_role_arn, var.worker_task_execution_role_arn]
    }

    actions = ["kms:Decrypt"]

    resources = [aws_kms_key.local_transcribe_secrets.arn]
  }

  # Required to allow the KMS key to be managed after creation: https://docs.aws.amazon.com/kms/latest/developerguide/key-policy-default.html#key-policy-default-allow-root-enable-iam
  statement {
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }

    actions = ["kms:*"]

    resources = [aws_kms_key.local_transcribe_secrets.arn]
  }
}

resource "aws_kms_key_policy" "kms_webapp_secrets_decrypt_policy" {
  key_id = aws_kms_key.local_transcribe_secrets.key_id
  policy = data.aws_iam_policy_document.kms_secrets_decrypt.json
}

resource "aws_iam_role_policy" "secret_access" {
  for_each = {
    frontend = var.frontend_task_execution_role_id
    backend  = var.backend_task_execution_role_id
    worker   = var.worker_task_execution_role_id
  }

  name = "${var.environment_name}-secret-access"
  role = each.value

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
        ]
      },
      {
        Action = [
          "ssm:GetParameters"
        ]
        Effect = "Allow"
        Resource = [
          aws_ssm_parameter.azure_apim_tenant_id.arn,
          aws_ssm_parameter.azure_apim_client_id.arn,
          aws_ssm_parameter.azure_apim_client_secret.arn,
          aws_ssm_parameter.azure_apim_scope.arn,
          aws_ssm_parameter.azure_apim_subscription_key.arn,
          aws_ssm_parameter.sentry_dsn.arn,
          aws_ssm_parameter.oidc_client_id.arn,
        ]
      }
    ]
  })
}
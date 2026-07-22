resource "aws_kms_key" "local_transcribe_secrets" {
  description         = "local-transcribe-secrets-${var.environment_name}"
  enable_key_rotation = true

  tags = {
    "terraform-plan-read" = true
  }
}

resource "aws_kms_alias" "local_transcribe_secrets" {
  target_key_id = aws_kms_key.local_transcribe_secrets.key_id
  name          = "alias/local-transcribe-secrets-${var.environment_name}"
}

resource "aws_kms_key" "rds_secrets" {
  description             = "KMS key for encrypting RDS secrets"
  enable_key_rotation     = true

}

resource "aws_kms_alias" "rds_secrets" {
  name          = "alias/${var.environment_name}-rds-secrets"
  target_key_id = aws_kms_key.rds_secrets.key_id
}

resource "aws_kms_key_policy" "rds-key" {
  key_id = aws_kms_key.rds_secrets.id
  policy = jsonencode({

    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "Enable IAM User Permissions"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "Allow Secrets Manager"
        Effect = "Allow"
        Principal = {
          Service = "secretsmanager.amazonaws.com"
        }
        Action = [
          "kms:Encrypt",
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:CallerAccount" = data.aws_caller_identity.current.account_id
          }
        }
        StringLike = {
          "kms:EncryptionContext:SecretARN" = [
            aws_secretsmanager_secret.database_secret.arn,
            var.master_user_secret_arn
          ]
        }

      }
    ]
  })

}

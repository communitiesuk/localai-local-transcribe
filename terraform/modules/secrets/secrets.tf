resource "aws_ssm_parameter" "oidc_client_name" {
  type   = "SecureString"
  key_id = aws_kms_key.local_transcribe_secrets.arn
  name   = "/local-transcribe/oidc_secrets/client_name"
  value  = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_ssm_parameter" "oidc_client_secret" {
  type   = "SecureString"
  key_id = aws_kms_key.local_transcribe_secrets.arn
  name   = "/local-transcribe/oidc_secrets/client_secret"
  value  = "placeholder" # Update value in SSM - Do not hardcode

  lifecycle {
    ignore_changes = [value]
  }
}

resource "aws_secretsmanager_secret" "database_password" {
  name                    = "tf-${var.environment_name}-local-transcribe-database-password"
  description             = "Password for local-transcribe backend database user"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.local_transcribe_secrets.arn
}

resource "random_password" "database_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id     = aws_secretsmanager_secret.database_password.id
  secret_string = random_password.database_password.result
}
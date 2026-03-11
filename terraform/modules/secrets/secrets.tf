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
resource "aws_secretsmanager_secret" "database_password" {
  name                    = "tf-${var.environment_name}-minute-database-password"
  description             = "Password for minute webapp database user"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}

resource "random_password" "database_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret_version" "database_password" {
  secret_id     = aws_secretsmanager_secret.database_password.id
  secret_string = random_password.database_password.result
}

resource "aws_secretsmanager_secret" "redis_password" {
  name                    = "tf-${var.environment_name}-minute-redis-password"
  description             = "Password for minute webapp to access redis"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}

resource "random_password" "redis_password" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret_version" "redis_password" {
  secret_id     = aws_secretsmanager_secret.redis_password.id
  secret_string = random_password.redis_password.result
}

resource "aws_secretsmanager_secret" "one_login_private_key" {
  name                    = "tf-${var.environment_name}-one-login-private-key"
  description             = "Private key for One Login"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}

resource "aws_secretsmanager_secret" "notify_api_key" {
  name                    = "tf-${var.environment_name}-notify-api-key"
  description             = "API key for Notify"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}

resource "aws_secretsmanager_secret" "os_api_key" {
  name                    = "tf-${var.environment_name}-os-api-key"
  description             = "API key for OS"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}

resource "aws_secretsmanager_secret" "epc_register_client_secret" {
  name                    = "tf-${var.environment_name}-minute-epc-client-secret"
  description             = "Client secret for the EPC register client secret"
  recovery_window_in_days = 0
  kms_key_id              = aws_kms_key.minute_webapp_secrets.arn
}
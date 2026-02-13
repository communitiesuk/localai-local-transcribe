output "database_password" {
  description = "Randomly generated password for database"
  value       = random_password.database_password
  sensitive   = true
}

output "database_password_secret_arn" {
  description = "ARN of the Secrets Manager secret that contains the database password"
  value       = aws_secretsmanager_secret.database_password.arn
}

output "redis_password" {
  description = "Randomly generated password for Redis"
  value       = random_password.redis_password
  sensitive   = true
}

output "secrets_kms_key_arn" {
  description = "ARN of the KMS key used to encrypt the secrets"
  value       = aws_kms_key.minute_webapp_secrets.arn
}

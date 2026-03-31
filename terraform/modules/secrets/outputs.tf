output "database_password" {
  description = "Randomly generated password for database"
  value       = random_password.database_password
  sensitive   = true
}

output "database_password_secret_arn" {
  description = "ARN of the Secrets Manager secret that contains the database password"
  value       = aws_secretsmanager_secret.database_password.arn
}

output "secrets_kms_key_arn" {
  description = "ARN of the KMS key used to encrypt the secrets"
  value       = aws_kms_key.local_transcribe_secrets.arn
}

output "oidc_client_id_name" {
  description = "SSM parameter name for the OIDC client ID."
  value       = aws_ssm_parameter.oidc_client_name.name
}

output "oidc_client_secret_name" {
  description = "SSM parameter name for the OIDC client secret."
  value       = aws_ssm_parameter.oidc_client_secret.name
}
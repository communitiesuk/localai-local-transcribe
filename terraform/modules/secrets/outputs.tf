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

output "internal_access_oidc_client_id_name" {
  description = "SSM parameter name for the Gov Internal Access OIDC client ID."
  value       = aws_ssm_parameter.oidc_client_id.name
}

output "internal_access_oidc_client_secret_name" {
  description = "SSM parameter name for the Gov Internal Access OIDC client secret."
  value       = aws_ssm_parameter.oidc_client_secret.name
}

output "azure_apim_tenant_id_arn" {
  description = "ARN of the SSM parameter containing the Azure APIM tenant ID"
  value       = aws_ssm_parameter.azure_apim_tenant_id.arn
}

output "azure_apim_client_id_arn" {
  description = "ARN of the SSM parameter containing the Azure APIM client ID"
  value       = aws_ssm_parameter.azure_apim_client_id.arn
}

output "azure_apim_client_secret_arn" {
  description = "ARN of the SSM parameter containing the Azure APIM client secret"
  value       = aws_ssm_parameter.azure_apim_client_secret.arn
}

output "azure_apim_scope_arn" {
  description = "ARN of the SSM parameter containing the Azure APIM OAuth scope"
  value       = aws_ssm_parameter.azure_apim_scope.arn
}

output "azure_apim_subscription_key_arn" {
  description = "ARN of the SSM parameter containing the Azure APIM subscription key"
  value       = aws_ssm_parameter.azure_apim_subscription_key.arn
}

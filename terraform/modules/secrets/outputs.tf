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

output "sentry_dsn_arn" {
  description = "ARN of the SSM parameter containing the Sentry DSN"
  value       = aws_ssm_parameter.sentry_dsn.arn
}

output "rds_master_secret_string" {
  description = "Secret string for the RDS master secret version"
  value       = data.aws_secretsmanager_secret_version.rds_master.secret_string
  sensitive   = true
}

output "govnotify_api_key_arn" {
  description = "ARN of the SSM parameter containing the GovNotify API key"
  value       = aws_ssm_parameter.govnotify_api_key.arn
}

output "govnotify_invite_template_id_arn" {
  description = "ARN of the SSM parameter containing the GovNotify invite template ID"
  value       = aws_ssm_parameter.govnotify_invite_template_id.arn
}

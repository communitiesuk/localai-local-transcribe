output "application_id" {
  description = "ID of the AppConfig application"
  value       = aws_appconfig_application.main.id
}

output "application_arn" {
  description = "ARN of the AppConfig application"
  value       = aws_appconfig_application.main.arn
}

output "environment_id" {
  description = "ID of the AppConfig environment"
  value       = aws_appconfig_environment.main.environment_id
}

output "configuration_profile_id" {
  description = "ID of the AppConfig configuration profile"
  value       = aws_appconfig_configuration_profile.main.configuration_profile_id
}

output "configuration_profile_arn" {
  description = "ARN of the AppConfig configuration profile"
  value       = aws_appconfig_configuration_profile.main.arn
}

output "kms_key_arn" {
  description = "ARN of the KMS key used to encrypt AppConfig hosted configuration data"
  value       = aws_kms_key.main.arn
}

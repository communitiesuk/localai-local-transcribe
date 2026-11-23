resource "aws_appconfig_deployment_strategy" "main" {
  name                           = "local-transcribe-app-config-deployment-strategy-${var.environment_name}"
  description                    = "AppConfig deployment strategy for ${var.environment_name}"
  deployment_duration_in_minutes = 5
  final_bake_time_in_minutes     = 30
  growth_factor                  = 30
  replicate_to                   = "NONE"
  tags = {
    type        = "AppConfig Deployment Strategy"
    Environment = "${var.environment_name}"
  }
}

resource "aws_appconfig_deployment" "main" {
  application_id           = aws_appconfig_application.main.id
  configuration_profile_id = aws_appconfig_configuration_profile.main.id
  configuration_version    = aws_appconfig_hosted_configuration_version.main.version_number
  deployment_strategy_id   = aws_appconfig_deployment_strategy.main.id
  environment_id           = aws_appconfig_environment.main.environment_id
  kms_key_identifier       = aws_kms_key.main.arn
  tags = {
    type        = "AppConfig Deployment"
    Environment = "${var.environment_name}"
  }

  lifecycle {
    ignore_changes = [
      configuration_version
    ]
  }
}


resource "aws_appconfig_application" "main" {
  name        = "local-transcribe-app-config-${var.environment_name}"
  description = "AppConfig application for ${var.environment_name}"
  tags = {
    type        = "AppConfig Application"
    Environment = "${var.environment_name}"
  }

}

resource "aws_appconfig_environment" "main" {
  application_id = aws_appconfig_application.main.id
  name           = "local-transcribe-app-config-environment-${var.environment_name}"
  description    = "AppConfig environment for ${var.environment_name}"
  tags = {
    type        = "AppConfig Environment"
    Environment = "${var.environment_name}"
  }
}

resource "aws_appconfig_configuration_profile" "main" {
  application_id = aws_appconfig_application.main.id
  name           = "local-transcribe-app-config-profile-${var.environment_name}"
  description    = "AppConfig configuration profile for ${var.environment_name}"
  location_uri   = "hosted"
  type           = "AWS.AppConfig.FeatureFlags"

  kms_key_identifier = aws_kms_key.main.arn

  tags = {
    type        = "AppConfig Configuration Profile"
    Environment = "${var.environment_name}"
  }
}

resource "aws_appconfig_hosted_configuration_version" "main" {
  application_id           = aws_appconfig_application.main.id
  configuration_profile_id = aws_appconfig_configuration_profile.main.id
  description              = "AppConfig feature flag configuration version for ${var.environment_name}"
  content_type             = "application/json"

  content = file("${path.module}/feature_flags.json")

  lifecycle {
    ignore_changes = [
      content
    ]
  }

}



// https://docs.aws.amazon.com/service-authorization/latest/reference/list_appconfig.html#list_appconfig-resources-for-iam-policies
data "aws_iam_policy_document" "app_config_read" {
  statement {
    effect = "Allow"
    actions = [
      "appconfig:StartConfigurationSession",
      "appconfig:GetLatestConfiguration",
    ]
    resources = [
      aws_appconfig_application.main.arn,
      "${aws_appconfig_application.main.arn}/*",
    ]
  }

  statement {
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [aws_kms_key.main.arn]
  }
}

resource "aws_iam_policy" "app_config_read" {
  name   = "local-transcribe-app-config-read-${var.environment_name}"
  policy = data.aws_iam_policy_document.app_config_read.json
}

# POLP permissions for CI to deploy feature_flags.json via the deploy_feature_flags
# script. https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-security.html
data "aws_iam_policy_document" "app_config_deploy" {
  statement {
    effect = "Allow"
    actions = [
      "appconfig:ListDeployments",
    ]
    resources = [
      aws_appconfig_application.main.arn,
      aws_appconfig_environment.main.arn,
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "appconfig:GetHostedConfigurationVersion",
      "appconfig:CreateHostedConfigurationVersion",
      "appconfig:ValidateConfiguration",
    ]
    resources = [
      aws_appconfig_application.main.arn,
      aws_appconfig_configuration_profile.main.arn,
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "appconfig:StartDeployment",
    ]
    resources = [
      aws_appconfig_application.main.arn,
      aws_appconfig_configuration_profile.main.arn,
      aws_appconfig_deployment_strategy.main.arn,
      aws_appconfig_environment.main.arn,
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*",
    ]
    resources = [aws_kms_key.main.arn]
  }
}

resource "aws_iam_policy" "app_config_deploy" {
  name   = "local-transcribe-app-config-deploy-${var.environment_name}"
  policy = data.aws_iam_policy_document.app_config_deploy.json
}

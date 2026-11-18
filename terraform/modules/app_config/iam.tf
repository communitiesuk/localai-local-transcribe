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
}

resource "aws_iam_policy" "app_config_read" {
  name   = "local-transcribe-app-config-read-${var.environment_name}"
  policy = data.aws_iam_policy_document.app_config_read.json
}

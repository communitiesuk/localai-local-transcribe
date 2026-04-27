resource "aws_cloudwatch_metric_alarm" "assume_role_with_saml" {
  alarm_name          = "assume-role-with-saml-${var.environment_name}"
  alarm_description   = "Someone has assumed an AWS role from AWS Console or from the command line using AWS Vault"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.assume_role_with_saml.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "unauthorized_api_calls" {
  alarm_name          = "unauthorized-api-calls-${var.environment_name}"
  alarm_description   = "There have been >=3 unauthorized calls to the AWS API in the last minute"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.unauthorized_api_calls.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 3
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "iam_policy_changes" {
  alarm_name          = "iam-policy-changes-${var.environment_name}"
  alarm_description   = "An IAM policy has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.iam_policy_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "cloudtrail_config_changes" {
  alarm_name          = "cloudtrail-config-changes-${var.environment_name}"
  alarm_description   = "CloudTrail configuration has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.cloudtrail_config_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "s3_bucket_policy_changes" {
  alarm_name          = "s3-bucket-policy-changes-${var.environment_name}"
  alarm_description   = "An S3 bucket policy has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.s3_bucket_policy_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "network_gateway_changes" {
  alarm_name          = "network-gateway-changes-${var.environment_name}"
  alarm_description   = "A network gateway has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.network_gateway_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "route_tables_changes" {
  alarm_name          = "route-tables-changes-${var.environment_name}"
  alarm_description   = "A routing table has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.route_tables_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "vpc_changes" {
  alarm_name          = "vpc-changes-${var.environment_name}"
  alarm_description   = "A VPC has been changed"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.vpc_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

resource "aws_cloudwatch_metric_alarm" "organization_changes" {
  alarm_name          = "organization-changes-${var.environment_name}"
  alarm_description   = "Changes have been made to the AWS organisation"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  metric_name         = aws_cloudwatch_log_metric_filter.organization_changes.name
  namespace           = "LogMetrics"
  evaluation_periods  = 1
  period              = 60
  threshold           = 1
  statistic           = "Sum"

  alarm_actions = [
    aws_sns_topic.alarm_sns_topic.arn,
  ]
}

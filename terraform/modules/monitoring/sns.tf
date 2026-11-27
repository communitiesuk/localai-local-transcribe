# non-sensitive
# tfsec:ignore:aws-sns-enable-topic-encryption
resource "aws_sns_topic" "alarm_sns_topic" {
  name              = "${var.environment_name}-alarm-sns-topic"
  display_name      = "Notifications for cloudwatch alarms in ${var.environment_name} environment"
  kms_master_key_id = aws_kms_key.main.arn

}

resource "aws_sns_topic_subscription" "alarm_email_subscription" {
  for_each  = nonsensitive(toset(keys(var.alarm_email_addresses)))
  topic_arn = aws_sns_topic.alarm_sns_topic.arn
  protocol  = "email"
  endpoint  = var.alarm_email_addresses[each.value]
}

# non-sensitive
# tfsec:ignore:aws-sns-enable-topic-encryption
resource "aws_sns_topic" "us_alarm_sns_topic" {
  name              = "${var.environment_name}-us-alarm-sns-topic"
  display_name      = "Notifications for cloudwatch alarms in ${var.environment_name} environment and us-east-1 region"
  provider          = aws.us-east-1
  kms_master_key_id = aws_kms_key.main.arn
}

resource "aws_sns_topic_subscription" "us_alarm_email_subscription" {
  for_each  = nonsensitive(toset(keys(var.alarm_email_addresses)))
  topic_arn = aws_sns_topic.us_alarm_sns_topic.arn
  protocol  = "email"
  endpoint  = var.alarm_email_addresses[each.value]
  provider  = aws.us-east-1
}

moved {
  from = aws_sns_topic_subscription.alarm_email_subscription
  to   = aws_sns_topic_subscription.alarm_email_subscription["primary"]
}

moved {
  from = aws_sns_topic_subscription.us_alarm_email_subscription
  to   = aws_sns_topic_subscription.us_alarm_email_subscription["primary"]
}

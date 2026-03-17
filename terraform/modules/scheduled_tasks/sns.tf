# non-sensitive
# tfsec:ignore:aws-sns-enable-topic-encryption
resource "aws_sns_topic" "alarm_scheduled_tasks_dead_letter_topic" {
  name         = "${var.environment_name}-scheduled-tasks-dead-letter-topic"
  display_name = "Notifications for scheduled tasks dead letters in ${var.environment_name} environment"
}

resource "aws_sns_topic_subscription" "alarm_email_subscription" {
  topic_arn = aws_sns_topic.alarm_scheduled_tasks_dead_letter_topic.arn
  protocol  = "email"
  endpoint  = var.alarm_email_address
}
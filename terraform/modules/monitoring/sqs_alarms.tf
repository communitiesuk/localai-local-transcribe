resource "aws_cloudwatch_metric_alarm" "transcription_dlq_alarm" {
  alarm_name          = "transcription-dlq-messages-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages detected in transcription DLQ"
  alarm_actions       = [aws_sns_topic.alarm_sns_topic.arn]

  dimensions = {
    QueueName = var.transcription_deadletter_queue_name
  }
}

resource "aws_cloudwatch_metric_alarm" "llm_dlq_alarm" {
  alarm_name          = "llm-dlq-messages-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Messages detected in llm DLQ"
  alarm_actions       = [aws_sns_topic.alarm_sns_topic.arn]

  dimensions = {
    QueueName = var.llm_deadletter_queue_name
  }
}

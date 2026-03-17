resource "aws_cloudwatch_metric_alarm" "task_invocation_failure" {
  alarm_name          = "${var.environment_name}-prsdb-task-invocation-failure"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "InvocationDroppedCount"
  namespace           = "AWS/Scheduler"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  dimensions = {
    "ScheduleGroup" = aws_scheduler_schedule_group.scheduled_tasks.name
  }

  alarm_description = <<-EOT
    EventBridge scheduler failed to start a scheduled ECS task.
    Check the dead letter queue ${aws_sqs_queue.scheduled_tasks_dead_letter_queue.name}
  EOT
  alarm_actions     = [aws_sns_topic.alarm_scheduled_tasks_dead_letter_topic.arn]
  ok_actions        = [aws_sns_topic.alarm_scheduled_tasks_dead_letter_topic.arn]
}

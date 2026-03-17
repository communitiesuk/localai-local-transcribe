# Non sensitive
# tfsec:ignore:aws-sqs-enable-queue-encryption
resource "aws_sqs_queue" "scheduled_tasks_dead_letter_queue" {
  name = "${var.environment_name}-prsdb-scheduled-tasks-dead-letter-queue"

  message_retention_seconds = 1209600 # 14 days, the maximum
}
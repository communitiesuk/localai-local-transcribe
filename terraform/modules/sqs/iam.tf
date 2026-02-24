resource "aws_iam_policy" "sqs_access" {
  name        = "${var.environment_name}-sqs-access"
  description = "Policy that allows full access to sqs queues"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
          "sqs:SendMessage",
          "sqs:DeleteMessage",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = [
          aws_sqs_queue.transcription_queue.arn,
          aws_sqs_queue.transcription_queue_deadletter.arn,
          aws_sqs_queue.llm_queue.arn,
          aws_sqs_queue.llm_queue_deadletter.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "backend_sqs_access" {
  role       = var.backend_task_execution_role_name
  policy_arn = aws_iam_policy.sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "worker_sqs_access" {
  role       = var.worker_task_execution_role_name
  policy_arn = aws_iam_policy.sqs_access.arn
}

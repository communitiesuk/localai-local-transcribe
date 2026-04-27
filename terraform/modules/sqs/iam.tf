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
  role       = var.backend_task_role_name
  policy_arn = aws_iam_policy.sqs_access.arn
}

resource "aws_iam_role_policy_attachment" "worker_sqs_access" {
  role       = var.worker_task_role_name
  policy_arn = aws_iam_policy.sqs_access.arn
}

locals {
  sqs_queues = {
    transcription_queue            = aws_sqs_queue.transcription_queue
    transcription_queue_deadletter = aws_sqs_queue.transcription_queue_deadletter
    llm_queue                      = aws_sqs_queue.llm_queue
    llm_queue_deadletter           = aws_sqs_queue.llm_queue_deadletter
  }
}

resource "aws_sqs_queue_policy" "enforce_tls" {
  for_each  = local.sqs_queues
  queue_url = each.value.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyNonTLS"
        Effect    = "Deny"
        Principal = "*"
        Action    = "sqs:*"
        Resource  = each.value.arn
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

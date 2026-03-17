resource "aws_iam_role" "scheduled_tasks" {
  name = "${var.environment_name}-scheduled-tasks"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduled_tasks" {
  name   = "${var.environment_name}-eventbridge-run-tasks"
  role   = aws_iam_role.scheduled_tasks.id
  policy = data.aws_iam_policy_document.scheduled_tasks.json
}

data "aws_iam_policy_document" "scheduled_tasks" {
  statement {
    actions = [
      "ecs:RunTask",
    ]
    resources = [
      for task in local.tasks : "${task.task_family_arn}:*"
    ]
  }
  statement {
    actions = [
      "iam:PassRole",
    ]
    resources = [var.task_role_arn, var.task_execution_role_arn]
    condition {
      test     = "StringLike"
      variable = "iam:PassedToService"
      values   = ["ecs-tasks.amazonaws.com"]
    }
  }
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.scheduled_tasks_dead_letter_queue.arn]
  }
}
data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "${var.environment_name}-ecs-task-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json
}

resource "aws_iam_role_policy_attachment" "task_execution_managed_policy" {
  role = aws_iam_role.ecs_task_execution.name
  # This is an aws managed policy for ecs task execution roles
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "task_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "frontend_ecs_task" {
  name               = "${var.environment_name}-frontend-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role.json
}

resource "aws_iam_role" "backend_ecs_task" {
  name               = "${var.environment_name}-backend-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role.json
}

resource "aws_iam_role" "worker_ecs_task" {
  name               = "${var.environment_name}-worker-ecs-task"
  assume_role_policy = data.aws_iam_policy_document.task_assume_role.json
}

data "aws_iam_policy_document" "allow_ecs_exec" {
  statement {
    actions = [
      "ssmmessages:CreateControlChannel",
      "ssmmessages:CreateDataChannel",
      "ssmmessages:OpenControlChannel",
      "ssmmessages:OpenDataChannel"
    ]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "allow_ecs_exec" {
  name   = "${var.environment_name}-allow-ecs-exec"
  policy = data.aws_iam_policy_document.allow_ecs_exec.json
}

resource "aws_iam_role_policy_attachment" "frontend_task_allow_ecs_exec" {
  role       = aws_iam_role.frontend_ecs_task.name
  policy_arn = aws_iam_policy.allow_ecs_exec.arn
}

resource "aws_iam_role_policy_attachment" "backend_task_allow_ecs_exec" {
  role       = aws_iam_role.backend_ecs_task.name
  policy_arn = aws_iam_policy.allow_ecs_exec.arn
}

resource "aws_iam_role_policy_attachment" "worker_task_allow_ecs_exec" {
  role       = aws_iam_role.worker_ecs_task.name
  policy_arn = aws_iam_policy.allow_ecs_exec.arn
}


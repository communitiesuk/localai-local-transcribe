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

data "aws_iam_policy_document" "push_images" {
  statement {
    actions = [
      "ecr:CompleteLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:InitiateLayerUpload",
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:ListImages"
    ]
    resources = [aws_ecr_repository.main.arn]
    effect    = "Allow"
  }

  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "push_images" {
  name   = "ecr-push-images"
  policy = data.aws_iam_policy_document.push_images.json
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

resource "aws_iam_role" "webapp_ecs_task" {
  name               = "${var.environment_name}-webapp-ecs-task"
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

resource "aws_iam_role_policy_attachment" "task_allow_ecs_exec" {
  role       = aws_iam_role.webapp_ecs_task.name
  policy_arn = aws_iam_policy.allow_ecs_exec.arn
}

data "aws_iam_policy_document" "describe_images" {
  statement {
    actions   = ["ecr:DescribeImages"]
    resources = [aws_ecr_repository.main.arn]
    effect    = "Allow"
  }

  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "describe_images" {
  name   = "ecr-describe-images"
  policy = data.aws_iam_policy_document.describe_images.json
}
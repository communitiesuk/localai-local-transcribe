data "aws_caller_identity" "current" {}

# Read only role for terraform plan
resource "aws_iam_role" "github_actions_terraform_plan" {
  name               = "github-actions-terraform-ci-plan-read-only"
  assume_role_policy = data.aws_iam_policy_document.github_actions_terraform_plan_assume_role.json
}

data "aws_iam_policy_document" "github_actions_terraform_plan_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.main.arn]
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    condition {
      test = "StringLike"
      values = [
        "repo:communitiesuk/prsdb-infra:*",
        "repo:communitiesuk/prsdb-webapp:*",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

data "aws_iam_policy" "terraform_state_read_only" {
  # Created in the terraform_backend module
  arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/tf-state-read-only"
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_plan_state_read" {
  role       = aws_iam_role.github_actions_terraform_plan.name
  policy_arn = data.aws_iam_policy.terraform_state_read_only.arn
}

data "aws_iam_policy" "read_only_access" {
  arn = "arn:aws:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_plan_read_only_access" {
  role       = aws_iam_role.github_actions_terraform_plan.name
  policy_arn = data.aws_iam_policy.read_only_access.arn
}


# Admin role for terraform apply
resource "aws_iam_role" "github_actions_terraform_admin" {
  name               = "github-actions-terraform-admin"
  assume_role_policy = data.aws_iam_policy_document.github_actions_terraform_admin_assume_role.json
}

data "aws_iam_policy_document" "github_actions_terraform_admin_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.main.arn]
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    condition {
      test = "StringLike"
      values = [
        "repo:communitiesuk/prsdb-infra:*",
        "repo:communitiesuk/prsdb-webapp:*",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

data "aws_iam_policy" "administrator_access" {
  arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

resource "aws_iam_role_policy_attachment" "github_actions_terraform_admin_access" {
  role       = aws_iam_role.github_actions_terraform_admin.name
  policy_arn = data.aws_iam_policy.administrator_access.arn
}

# ECR Push role for webapp repo
data "aws_iam_policy_document" "github_actions_push_ecr_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.main.arn]
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    condition {
      test = "StringLike"
      values = [
        "repo:communitiesuk/prsdb-webapp:*",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

resource "aws_iam_role" "push_image" {
  name               = "${var.environment_name}-push-image"
  assume_role_policy = data.aws_iam_policy_document.github_actions_push_ecr_assume_role.json
}

resource "aws_iam_role_policy_attachment" "allow_push_image_policy_attachment" {
  role       = aws_iam_role.push_image.name
  policy_arn = var.push_ecr_image_policy_arn
}

# RDS access role for webapp repo
data "aws_iam_policy_document" "github_actions_rds_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.main.arn]
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    condition {
      test = "StringLike"
      values = [
        "repo:communitiesuk/prsdb-webapp:*",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

data "aws_iam_policy_document" "ssm_port_forwarding" {
  statement {
    effect = "Allow"
    actions = [
      "ssm:DescribeSessions",
      "ec2:DescribeInstances",
    ]
    resources = [
      "*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:TerminateSession",
      "ssm:ResumeSession",
    ]
    resources = [
      "arn:aws:ssm:eu-west-2:${data.aws_caller_identity.current.account_id}:session/GitHubActions-*",
    ]
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:StartSession",
    ]
    resources = concat(
      var.bastion_host_arns,
      ["arn:aws:ssm:eu-west-2::document/AWS-StartPortForwardingSessionToRemoteHost"],
    )
  }

  statement {
    effect = "Allow"
    actions = [
      "ssm:GetParameter",
    ]
    resources = [var.db_username_ssm_parameter_arn, var.db_url_ssm_parameter_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [var.db_password_secret_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
    ]
    resources = [var.secrets_kms_key_arn]
  }
}

data "aws_iam_policy_document" "update_ecs_service" {
  count = var.task_definition_created ? 1 : 0
  statement {
    effect = "Allow"
    actions = [
      "ecs:UpdateService",
    ]
    resources = [var.ecs_service_arn]
  }

  statement {
    effect = "Allow"
    actions = [
      "iam:PassRole",
    ]
    resources = [var.ecs_task_execution_role_arn, var.webapp_ecs_task_role_arn]
  }
}

resource "aws_iam_policy" "ssm_port_forwarding" {
  name        = "${var.environment_name}-ssm-port-forwarding"
  description = "Policy that allows SSM port forwarding for RDS access"
  policy      = data.aws_iam_policy_document.ssm_port_forwarding.json
}

resource "aws_iam_policy" "update_ecs_service" {
  count       = var.task_definition_created ? 1 : 0
  name        = "${var.environment_name}-update-ecs-service"
  description = "Policy that allows updating ECS service"
  policy      = data.aws_iam_policy_document.update_ecs_service[0].json
}

resource "aws_iam_role" "rds_access" {
  name               = "${var.environment_name}-rds-access"
  assume_role_policy = data.aws_iam_policy_document.github_actions_rds_assume_role.json
}

resource "aws_iam_role_policy_attachment" "allow_rds_access_policy_attachment" {
  role       = aws_iam_role.rds_access.name
  policy_arn = aws_iam_policy.ssm_port_forwarding.arn
}

resource "aws_iam_role_policy_attachment" "allow_update_ecs_service_policy_attachment" {
  count      = var.task_definition_created ? 1 : 0
  role       = aws_iam_role.rds_access.name
  policy_arn = aws_iam_policy.update_ecs_service[0].arn
}

# ECR Describe Images role for infra repo
data "aws_iam_policy_document" "github_actions_assume_ecr_describe_images_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.main.arn]
    }

    condition {
      test     = "StringEquals"
      values   = ["sts.amazonaws.com"]
      variable = "token.actions.githubusercontent.com:aud"
    }

    condition {
      test     = "StringLike"
      values   = ["repo:communitiesuk/prsdb-infra:*"]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

resource "aws_iam_role" "ecr_describe_images" {
  name               = "${var.environment_name}-ecr-describe-images"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume_ecr_describe_images_role.json
}

resource "aws_iam_role_policy_attachment" "ecr_describe_images" {
  role       = aws_iam_role.ecr_describe_images.name
  policy_arn = var.ecr_describe_images_policy_arn
}
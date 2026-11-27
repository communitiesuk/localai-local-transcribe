data "aws_caller_identity" "current" {}

locals {
  github_repository_subject = "repo:communitiesuk/localai-local-transcribe"

  # Who may assume the plan role. A plan reads the Terraform state, which holds this
  # environment's secrets, so anything listed here can read those secrets.
  terraform_plan_subjects = concat(
    # The deploy workflow, running on the deployment branch.
    ["${local.github_repository_subject}:ref:refs/heads/${var.deployment_branch}"],
    # If `allow_plan_from_pull_requests` is set, then any pull request in this repository.
    # Pull requests from forks cannot get a token.
    var.allow_plan_from_pull_requests ? ["${local.github_repository_subject}:pull_request"] : [],
    # If `plan_github_environment` is set, jobs that run in this GitHub environment, which has required reviewers.
    var.plan_github_environment != null ? ["${local.github_repository_subject}:environment:${var.plan_github_environment}"] : [],
  )
}

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
      test     = "StringLike"
      values   = local.terraform_plan_subjects
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
      test     = "StringLike"
      values   = ["repo:communitiesuk/localai-local-transcribe:ref:refs/heads/${var.deployment_branch}"]
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

# Least-privilege role for the deploy-feature-flags CI job.
resource "aws_iam_role" "github_actions_appconfig_deploy" {
  name               = "github-actions-appconfig-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_actions_appconfig_deploy_assume_role.json
}

data "aws_iam_policy_document" "github_actions_appconfig_deploy_assume_role" {
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
      values   = ["repo:communitiesuk/localai-local-transcribe:ref:refs/heads/${var.deployment_branch}"]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

resource "aws_iam_role_policy_attachment" "github_actions_appconfig_deploy_state_read" {
  role       = aws_iam_role.github_actions_appconfig_deploy.name
  policy_arn = data.aws_iam_policy.terraform_state_read_only.arn
}

resource "aws_iam_role_policy_attachment" "github_actions_appconfig_deploy_access" {
  role       = aws_iam_role.github_actions_appconfig_deploy.name
  policy_arn = var.app_config_deploy_policy_arn
}

# ECR Push role
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
        "repo:communitiesuk/localai-local-transcribe:ref:refs/heads/${var.deployment_branch}",
      ]
      variable = "token.actions.githubusercontent.com:sub"
    }
  }
}

resource "aws_iam_role" "push_image" {
  name               = "${var.environment_name}-push-image"
  assume_role_policy = data.aws_iam_policy_document.github_actions_push_ecr_assume_role.json
}

resource "aws_iam_role_policy_attachment" "allow_push_frontend_image_policy_attachment" {
  role       = aws_iam_role.push_image.name
  policy_arn = var.push_frontend_ecr_image_policy_arn
}

resource "aws_iam_role_policy_attachment" "allow_push_backend_image_policy_attachment" {
  role       = aws_iam_role.push_image.name
  policy_arn = var.push_backend_ecr_image_policy_arn
}

resource "aws_iam_role_policy_attachment" "allow_push_worker_image_policy_attachment" {
  role       = aws_iam_role.push_image.name
  policy_arn = var.push_worker_ecr_image_policy_arn
}

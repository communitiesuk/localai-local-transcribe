data "aws_iam_policy_document" "push_frontend_images" {
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
    resources = [aws_ecr_repository.frontend.arn]
    effect    = "Allow"
  }

  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "push_frontend_images" {
  name   = "ecr-push-frontend-images"
  policy = data.aws_iam_policy_document.push_frontend_images.json
}

data "aws_iam_policy_document" "push_backend_images" {
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
    resources = [aws_ecr_repository.backend.arn]
    effect    = "Allow"
  }

  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "push_backend_images" {
  name   = "ecr-push-backend-images"
  policy = data.aws_iam_policy_document.push_backend_images.json
}

data "aws_iam_policy_document" "push_worker_images" {
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
    resources = [aws_ecr_repository.worker.arn]
    effect    = "Allow"
  }

  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
    effect    = "Allow"
  }
}

resource "aws_iam_policy" "push_worker_images" {
  name   = "ecr-push-worker-images"
  policy = data.aws_iam_policy_document.push_worker_images.json
}

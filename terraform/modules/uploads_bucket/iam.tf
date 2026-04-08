data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "ecs_bucket_access" {
  statement {
    effect = "Allow"
    actions = [
      "s3:Get*",
      "s3:List*",
      "s3:Put*",
      "s3:Delete*",
    ]
    resources = [
      "${module.uploads_bucket.bucket_arn}/app_data/*",
      "${module.uploads_bucket.bucket_arn}/app_data",
    ]
  }
}

resource "aws_iam_policy" "ecs_bucket_access" {
  name   = "${var.environment_name}-ecs-bucket-access"
  policy = data.aws_iam_policy_document.ecs_bucket_access.json
}

resource "aws_iam_role_policy_attachment" "ecs_bucket_access" {
  role       = var.worker_task_execution_role_name
  policy_arn = aws_iam_policy.ecs_bucket_access.arn
}

resource "aws_iam_role_policy_attachment" "ecs_bucket_access_backend" {
  role       = var.backend_task_role_name
  policy_arn = aws_iam_policy.ecs_bucket_access.arn
}
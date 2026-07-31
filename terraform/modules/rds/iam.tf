data "aws_region" "current" {}

resource "aws_iam_policy" "rds_iam_connect" {
  name        = "${var.environment_name}-rds-iam-connect"
  description = "Allows generating IAM auth tokens for the app DB user"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "rds-db:connect"
      Resource = "arn:aws:rds-db:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:dbuser:${aws_db_instance.main.resource_id}/${var.master_database_username}"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "backend_db_connect" {
  role       = var.backend_task_role_name
  policy_arn = aws_iam_policy.rds_iam_connect.arn
}

resource "aws_iam_role_policy_attachment" "worker_db_connect" {
  role       = var.worker_task_role_name
  policy_arn = aws_iam_policy.rds_iam_connect.arn
}

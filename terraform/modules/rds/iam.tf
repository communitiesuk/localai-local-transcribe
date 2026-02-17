resource "aws_iam_policy" "rds_data_access" {
  name        = "${var.environment_name}-rds-data-access"
  description = "Policy that allows full access to RDS"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-data:ExecuteSql",
          "rds-data:ExecuteStatement",
          "rds-data:BatchExecuteStatement",
          "rds-data:BeginTransaction",
          "rds-data:CommitTransaction",
          "rds-data:RollbackTransaction"
        ]
        Resource = aws_db_instance.main.arn
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "webapp_database_access" {
  role       = var.webapp_task_execution_role_name
  policy_arn = aws_iam_policy.rds_data_access.arn
}
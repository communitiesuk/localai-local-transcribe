#TODO: PRSD-1115 - add customer managed KMS key
#tfsec:ignore:aws-cloudwatch-log-group-customer-key
resource "aws_cloudwatch_log_group" "frontend_log_group" {
  name              = "${var.environment_name}-frontend"
  retention_in_days = 60

  tags = {
    Application = var.environment_name
  }
}

resource "aws_cloudwatch_log_group" "backend_log_group" {
  name              = "${var.environment_name}-backend"
  retention_in_days = 60

  tags = {
    Application = var.environment_name
  }
}

resource "aws_cloudwatch_log_group" "worker_log_group" {
  name              = "${var.environment_name}-worker"
  retention_in_days = 60

  tags = {
    Application = var.environment_name
  }
}

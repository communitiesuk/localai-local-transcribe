#TODO: PRSD-1115 - add customer managed KMS key
#tfsec:ignore:aws-cloudwatch-log-group-customer-key
resource "aws_cloudwatch_log_group" "webapp_log_group" {
  name              = "${var.environment_name}-${var.task_name}"
  retention_in_days = 60

  tags = {
    Application = var.environment_name
  }
}

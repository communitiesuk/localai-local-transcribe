resource "aws_flow_log" "vpc_accepted" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs.arn
  log_destination = module.vpc_flow_logs_accepted.log_group_arn
  traffic_type    = "ACCEPT"
  vpc_id          = aws_vpc.main.id
}

resource "aws_flow_log" "vpc_rejected" {
  iam_role_arn    = aws_iam_role.vpc_flow_logs.arn
  log_destination = module.vpc_flow_logs_rejected.log_group_arn
  traffic_type    = "REJECT"
  vpc_id          = aws_vpc.main.id
}

module "vpc_flow_logs_accepted" {
  source = "../../modules/encrypted_log_group"

  log_group_name     = "vpc-flow-logs-accepted-${var.environment_name}"
  log_retention_days = var.vpc_flow_cloudwatch_log_expiration_days
}

module "vpc_flow_logs_rejected" {
  source = "../../modules/encrypted_log_group"

  log_group_name     = "vpc-flow-logs-rejected-${var.environment_name}"
  log_retention_days = var.vpc_flow_cloudwatch_log_expiration_days
}

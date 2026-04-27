resource "aws_flow_log" "bastion_ssm_patch" {
  count           = length(var.bastion_subnet_ids)
  iam_role_arn    = aws_iam_role.bastion_logs.arn
  log_destination = module.bastion_logs.log_group_arn
  traffic_type    = "ALL"
  subnet_id       = var.bastion_subnet_ids[count.index]
  tags = {
    Name = "${var.environment_name}-bastion-${count.index + 1}"
  }
}

module "bastion_logs" {
  source = "../../modules/encrypted_log_group"

  log_group_name     = "${var.environment_name}-bastion-ssm-patch-logs"
  log_retention_days = var.bastion_ssm_patch_cloudwatch_log_expiration_days
}
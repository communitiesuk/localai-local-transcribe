resource "aws_security_group" "main" {
  name        = "${var.environment_name}-rds"
  description = "RDS security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "ingress_for_ssm_port_forwarding" {
  description                  = "Allow ingress on port 5432 from the bastion"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = var.bastion_group_id
  security_group_id            = aws_security_group.main.id
}
resource "aws_security_group" "main" {
  name        = "${var.environment_name}-rds"
  description = "RDS security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "lambda_rotation" {
  name        = "${var.environment_name}-lambda-rotation-sg"
  description = "ECS security group"
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

resource "aws_vpc_security_group_ingress_rule" "rds_allow_rotation_lambda" {
  for_each = toset(aws_db_instance.main.vpc_security_group_ids)

  description                  = "Allow rotation Lambda to connect to the db"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.lambda_rotation.id
  security_group_id            = each.value
}
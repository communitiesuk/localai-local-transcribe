resource "aws_security_group" "frontend" {
  name        = "${var.environment_name}-frontend-ecs"
  description = "ECS security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "backend" {
  name        = "${var.environment_name}-backend-ecs"
  description = "ECS security group"
  vpc_id      = var.vpc_id

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_security_group" "worker" {
  name        = "${var.environment_name}-worker-ecs"
  description = "ECS security group"
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

resource "aws_vpc_security_group_ingress_rule" "frontend_ingress_from_bastion" {
  description                  = "Allow frontend ingress on port ${var.frontend_port} from the bastion"
  ip_protocol                  = "tcp"
  from_port                    = var.frontend_port
  to_port                      = var.frontend_port
  referenced_security_group_id = var.bastion_sg_id
  security_group_id            = aws_security_group.frontend.id
}

resource "aws_vpc_security_group_ingress_rule" "frontend_ingress_from_load_balancer" {
  description                  = "Allow frontend ingress on port ${var.frontend_port} from the load balancer"
  ip_protocol                  = "tcp"
  from_port                    = var.frontend_port
  to_port                      = var.frontend_port
  referenced_security_group_id = var.lb_security_group_id
  security_group_id            = aws_security_group.frontend.id
}

resource "aws_vpc_security_group_egress_rule" "load_balancer_egress_to_frontend" {
  description                  = "Allow load balancer egress on port ${var.frontend_port} to the frontend"
  ip_protocol                  = "tcp"
  from_port                    = var.frontend_port
  to_port                      = var.frontend_port
  referenced_security_group_id = aws_security_group.frontend.id
  security_group_id            = var.lb_security_group_id
}

resource "aws_vpc_security_group_ingress_rule" "backend_ingress_from_frontend" {
  description                  = "Allow backend ingress on port ${var.backend_port} from the frontend"
  ip_protocol                  = "tcp"
  from_port                    = var.backend_port
  to_port                      = var.backend_port
  referenced_security_group_id = aws_security_group.frontend.id
  security_group_id            = aws_security_group.backend.id
}

resource "aws_vpc_security_group_egress_rule" "frontend_egress_to_backend" {
  description                  = "Allow frontend egress on port ${var.backend_port} to the backend"
  ip_protocol                  = "tcp"
  from_port                    = var.backend_port
  to_port                      = var.backend_port
  referenced_security_group_id = aws_security_group.backend.id
  security_group_id            = aws_security_group.frontend.id
}

resource "aws_vpc_security_group_egress_rule" "backend_egress_to_db" {
  description                  = "Allow backend egress on port ${var.database_port} to the database"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = var.db_security_group_id
  security_group_id            = aws_security_group.backend.id
}

resource "aws_vpc_security_group_ingress_rule" "backend_to_db_ingress" {
  description                  = "Allow database ingress on port ${var.database_port} from the backend"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = aws_security_group.backend.id
  security_group_id            = var.db_security_group_id
}

resource "aws_vpc_security_group_egress_rule" "worker_egress_to_db" {
  description                  = "Allow worker egress on port ${var.database_port} to the database"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = var.db_security_group_id
  security_group_id            = aws_security_group.worker.id
}

resource "aws_vpc_security_group_ingress_rule" "worker_to_db_ingress" {
  description                  = "Allow database ingress on port ${var.database_port} from the worker"
  ip_protocol                  = "tcp"
  from_port                    = var.database_port
  to_port                      = var.database_port
  referenced_security_group_id = aws_security_group.worker.id
  security_group_id            = var.db_security_group_id
}

resource "aws_vpc_security_group_egress_rule" "frontend_http_egress" {
  description       = "Allow frontend http egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  security_group_id = aws_security_group.frontend.id
}

resource "aws_vpc_security_group_egress_rule" "frontend_https_egress" {
  description       = "Allow frontend https egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  security_group_id = aws_security_group.frontend.id
}

resource "aws_vpc_security_group_egress_rule" "backend_http_egress" {
  description       = "Allow backend http egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  security_group_id = aws_security_group.backend.id
}

resource "aws_vpc_security_group_egress_rule" "backend_https_egress" {
  description       = "Allow backend https egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  security_group_id = aws_security_group.backend.id
}

resource "aws_vpc_security_group_egress_rule" "worker_http_egress" {
  description       = "Allow worker http egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
  security_group_id = aws_security_group.worker.id
}

resource "aws_vpc_security_group_egress_rule" "worker_https_egress" {
  description       = "Allow worker https egress to any public internet IP address"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
  security_group_id = aws_security_group.worker.id
}

resource "aws_vpc_security_group_ingress_rule" "rds_allow_rotation_lambda" {
  for_each = toset(var.db_vpc_security_group)

  description                  = "Allow rotation Lambda to connect to the db"
  ip_protocol                  = "tcp"
  from_port                    = 5432
  to_port                      = 5432
  referenced_security_group_id = aws_security_group.lambda_rotation.id
  security_group_id            = each.value
}
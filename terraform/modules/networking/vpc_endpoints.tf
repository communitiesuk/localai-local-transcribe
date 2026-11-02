resource "aws_security_group" "aws_service_vpc_endpoints" {
  name        = "vpc-endpoints-${var.environment_name}"
  description = "VPC Endpoint security group"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Connections from VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }
}

locals {
  # This list must be append-only to avoid terraform tearing down and (trying to) recreate the endpoints - this fails due to DNS propagation time
  vpc_endpoint_services = [
    "ssm",
    "ssmmessages",
    "ec2messages",
    "secretsmanager",
    "ecr.api",
    "ecr.dkr",
    "ecs",
    "ecs-agent",
    "ecs-telemetry",
    "kms",
    "ec2",
    "monitoring",
    "logs",
    "cloudtrail",
    "sns",
    "sqs",
  ]
}

data "aws_vpc_endpoint_service" "vpc_endpoints" {
  count        = length(local.vpc_endpoint_services)
  service      = local.vpc_endpoint_services[count.index]
  service_type = "Interface"
}


resource "aws_vpc_endpoint" "vpc_endpoints" {
  vpc_id              = aws_vpc.main.id
  count               = length(data.aws_vpc_endpoint_service.vpc_endpoints)
  service_name        = data.aws_vpc_endpoint_service.vpc_endpoints[count.index].service_name
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private_subnet[*].id
  security_group_ids  = [aws_security_group.aws_service_vpc_endpoints.id]
  private_dns_enabled = true
}

data "aws_vpc_endpoint_service" "s3_gateway" {
  service      = "s3"
  service_type = "Gateway"
}

moved {
  from = aws_vpc_endpoint.s3_endpoint
  to   = aws_vpc_endpoint.s3_gateway
}

resource "aws_vpc_endpoint" "s3_gateway" {
  vpc_id            = aws_vpc.main.id
  service_name      = data.aws_vpc_endpoint_service.s3_gateway.service_name
  vpc_endpoint_type = "Gateway"

  route_table_ids = [
    aws_route_table.to_nat_gateway.id,
  ]

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "s3-gateway-endpoint-${var.environment_name}"
  }
}

resource "aws_security_group" "bastion" {
  name        = "${var.environment_name}-bastion"
  description = "Security group for SSM bastion in ${var.environment_name}"

  vpc_id = var.main_vpc_id

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "Allow bastion access to vpc endpoints to allow for SSM"
  }

  #tfsec:ignore:aws-ec2-no-public-egress-sgr - required for SSM patch manager to access Amazon Linux package repositories
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow bastion access to Amazon Linux package repositories via NAT Gateway"
  }

  egress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr_block]
    description = "Allow bastion access to postgres port within the VPC"
  }
}

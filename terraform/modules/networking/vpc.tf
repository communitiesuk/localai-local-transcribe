resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr_block
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "local-transcribe-vpc-${var.environment_name}"
  }
}

resource "aws_default_security_group" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.environment_name}-default-sg-rules-restricted"
    Description = "Locked default SG - no ingress or egress rules"
  }

}

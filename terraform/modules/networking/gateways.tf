resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "internet-gateway-${var.environment_name}"
  }
}

resource "aws_eip" "nat_gateway" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_gateway" {
  allocation_id = aws_eip.nat_gateway.id
  subnet_id     = aws_subnet.nat_gateway.id

  tags = {
    Name = "nat-gateway-${var.environment_name}"
  }
}
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
  count = var.number_of_availability_zones
  domain = "vpc"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_nat_gateway" "nat_gateway" {
  vpc_id = aws_vpc.main.id
  availability_mode = "regional"

  dynamic "availability_zone_address" {
    for_each = range(var.number_of_availability_zones)
    content {
      allocation_ids = [aws_eip.nat_gateway[availability_zone_address.value].id]
      availability_zone = data.aws_availability_zones.available.names[availability_zone_address.value]
    }
  }

  tags = {
    Name = "nat-gateway-${var.environment_name}"
  }
}
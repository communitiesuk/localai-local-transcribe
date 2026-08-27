locals {
  # Using this set (rather than indexing into the availability zone array directly) allows us to
  # ensure each availability zone always gets the same eip as we reference by key rather than order
  nat_availability_zones = toset(slice(data.aws_availability_zones.available.names, 0, var.number_of_availability_zones))
}

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
  for_each = local.nat_availability_zones
  domain   = "vpc"

  # We add prevent destroy to guard against any eip changes.
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_nat_gateway" "regional_nat_gateway" {
  vpc_id            = aws_vpc.main.id
  availability_mode = "regional"

  dynamic "availability_zone_address" {
    for_each = local.nat_availability_zones
    content {
      allocation_ids    = [aws_eip.nat_gateway[availability_zone_address.key].id]
      availability_zone = availability_zone_address.key
    }
  }

  tags = {
    Name = "nat-gateway-${var.environment_name}"
  }
}
# Public subnets route internet traffic to Internet Gateway
resource "aws_route_table" "to_internet_gateway" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "to-igw-route-table-${var.environment_name}"
  }
}

resource "aws_route_table_association" "public" {
  count          = var.number_of_availability_zones
  subnet_id      = aws_subnet.public_subnet[count.index].id
  route_table_id = aws_route_table.to_internet_gateway.id
}

# Private subnets should route internet traffic to the NAT gateway
resource "aws_route_table" "to_nat_gateway" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "to-nat-gateway-route-table-${var.environment_name}"
  }
}

resource "aws_route" "to_nat_gateway" {
  route_table_id         = aws_route_table.to_nat_gateway.id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_gateway.id
}

resource "aws_route_table_association" "private" {
  count          = var.number_of_availability_zones
  subnet_id      = aws_subnet.private_subnet[count.index].id
  route_table_id = aws_route_table.to_nat_gateway.id
}


# Isolated subnets should only have access to the VPC
resource "aws_route_table" "local_only" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "local-only-route-table-${var.environment_name}"
  }
}

resource "aws_route_table_association" "isolated" {
  count          = var.number_of_isolated_subnets
  subnet_id      = aws_subnet.isolated_subnet[count.index].id
  route_table_id = aws_route_table.local_only.id
}

# NAT gateway should send internet bound traffic out to the gateway
resource "aws_route_table" "nat_gateway_subnet_route_table" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "nat-gateway-subnet-route-table-${var.environment_name}"
  }
}

resource "aws_route" "nat_gateway_to_internet" {
  route_table_id         = aws_route_table.nat_gateway_subnet_route_table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_route_table_association" "nat_gateway" {
  subnet_id      = aws_subnet.nat_gateway.id
  route_table_id = aws_route_table.nat_gateway_subnet_route_table.id
}
data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  nat_gateway_cidr_10 = cidrsubnet(aws_vpc.main.cidr_block, 6, 0) # 0.0/22 - public
  public_cidr_10      = cidrsubnet(aws_vpc.main.cidr_block, 6, 1) # 4.0/22 - for alb listeners
  firewall_cidr_10    = cidrsubnet(aws_vpc.main.cidr_block, 6, 2) # 8.0/22
  private_cidr_10     = cidrsubnet(aws_vpc.main.cidr_block, 6, 3) # 12.0/22- ecs and bastion host
  isolated_cidr_10    = cidrsubnet(aws_vpc.main.cidr_block, 6, 4) # 16.0/22
}

resource "aws_subnet" "nat_gateway" {
  availability_zone = data.aws_availability_zones.available.names[0]
  cidr_block        = local.nat_gateway_cidr_10
  vpc_id            = aws_vpc.main.id
  tags              = { Name = "nat-gateway-${var.environment_name}" }
}

# tfsec:ignore:aws-ec2-no-public-ip-subnet
resource "aws_subnet" "public_subnet" {
  count                   = var.number_of_availability_zones
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  cidr_block              = cidrsubnet(local.public_cidr_10, 2, count.index)
  vpc_id                  = aws_vpc.main.id
  map_public_ip_on_launch = true
  tags                    = { Name = "public-subnet-${var.environment_name}-${data.aws_availability_zones.available.names[count.index]}" }
}

resource "aws_subnet" "firewall" {
  availability_zone = data.aws_availability_zones.available.names[0]
  cidr_block        = local.firewall_cidr_10
  vpc_id            = aws_vpc.main.id
  tags              = { Name = "vpc-network-firewall-subnet-${var.environment_name}" }
}

resource "aws_subnet" "private_subnet" {
  count             = var.number_of_availability_zones
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(local.private_cidr_10, 2, count.index)
  vpc_id            = aws_vpc.main.id
  tags              = { Name = "vpc-private-subnet-${var.environment_name}-${data.aws_availability_zones.available.names[count.index]}" }
}

resource "aws_subnet" "isolated_subnet" {
  count             = var.number_of_isolated_subnets
  availability_zone = data.aws_availability_zones.available.names[count.index]
  cidr_block        = cidrsubnet(local.isolated_cidr_10, 2, count.index)
  vpc_id            = aws_vpc.main.id
  tags              = { Name = "vpc-isolated-subnet-${var.environment_name}-${data.aws_availability_zones.available.names[count.index]}" }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.environment_name}-db-subnet-group"
  subnet_ids = aws_subnet.isolated_subnet[*].id
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.environment_name}-redis-subnet-group"
  subnet_ids = aws_subnet.isolated_subnet[*].id
}

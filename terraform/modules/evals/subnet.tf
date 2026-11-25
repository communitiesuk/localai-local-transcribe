locals {
  # The networking module uses ranges 1 to 4 of the VPC's address space, each a /22 block.
  # Range 5 is the next free block, so the evals subnet does not overlap any product subnet.
  # Like the product subnets, the evals subnet is a /24 block carved from the start of its range.
  evals_private_cidr = cidrsubnet(cidrsubnet(var.vpc_cidr_block, 6, 5), 2, 0)
}

# Private subnet for evals tasks. It has no public addresses and is separate from the web
# application's private subnets, so evals traffic can be controlled on its own later.
resource "aws_subnet" "evals_private" {
  availability_zone = var.availability_zone
  cidr_block        = local.evals_private_cidr
  vpc_id            = var.vpc_id
  tags              = { Name = "evals-private-subnet-${var.environment_name}-${var.availability_zone}" }
}

# A new subnet falls back to the VPC's main route table, which only reaches the VPC itself.
# Using the product's private route table sends internet traffic through the NAT gateway,
# which is how evals tasks reach the AI Gateway.
resource "aws_route_table_association" "evals_private" {
  subnet_id      = aws_subnet.evals_private.id
  route_table_id = var.private_route_table_id
}

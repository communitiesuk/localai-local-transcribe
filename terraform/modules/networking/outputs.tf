output "vpc" {
  value       = aws_vpc.main
  description = "The AWS VPC"
}

output "nat_gateway_ips" {
  value       = { for k, v in aws_eip.nat_gateway : k => v.public_ip }
  description = "The IP address of the NAT gateway"
}

output "public_subnets" {
  value       = aws_subnet.public_subnet
  description = "Public /22 subnets for alb listeners"
}

output "private_subnets" {
  value       = aws_subnet.private_subnet
  description = "Private /22 subnets for ECS and bastian host"
}

output "private_route_table_id" {
  value       = aws_route_table.to_nat_gateway.id
  description = "Id of the route table that sends internet traffic from private subnets to the NAT gateway"
}

output "isolated_subnets" {
  value       = aws_subnet.isolated_subnet
  description = "var.number_of_isolated_subnets /22 subnets for db and redis - 2 required when using multi-AZ rds"
}

output "db_subnet_group_name" {
  value       = aws_db_subnet_group.main.name
  description = "Name of the db subnet group"
}

output "redis_subnet_group_name" {
  value       = aws_elasticache_subnet_group.main.name
  description = "Name of the redis subnet group"
}


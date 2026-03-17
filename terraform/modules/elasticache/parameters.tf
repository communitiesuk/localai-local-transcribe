resource "aws_ssm_parameter" "redis_url" {
  name  = "${var.environment_name}-prsdb-redis-url"
  type  = "String"
  value = aws_elasticache_replication_group.main.primary_endpoint_address
}

resource "aws_ssm_parameter" "redis_port" {
  name  = "${var.environment_name}-prsdb-redis-port"
  type  = "String"
  value = var.redis_port
}
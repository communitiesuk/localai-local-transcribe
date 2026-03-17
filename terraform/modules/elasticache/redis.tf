data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  preferred_cache_cluster_azs = var.highly_available ? slice(data.aws_availability_zones.available.names[*], 0, 2) : [data.aws_availability_zones.available.names[0]]
}

resource "aws_elasticache_replication_group" "main" {
  at_rest_encryption_enabled  = true
  auth_token                  = var.redis_password
  auto_minor_version_upgrade  = true
  automatic_failover_enabled  = var.highly_available ? true : false
  description                 = "Redis replication group, consisting of a single node, or a primary node and a replica."
  engine                      = "redis"
  engine_version              = "7.1" # Unlike RDS, this should not cause state drift
  final_snapshot_identifier   = "${var.environment_name}-database-final-snapshot"
  maintenance_window          = var.maintenance_window
  multi_az_enabled            = var.highly_available ? true : false
  node_type                   = var.node_type
  num_cache_clusters          = var.highly_available ? 2 : 1
  port                        = var.redis_port
  preferred_cache_cluster_azs = local.preferred_cache_cluster_azs
  replication_group_id        = "${var.environment_name}-redis-replication-group"
  security_group_ids          = [aws_security_group.redis.id]
  snapshot_retention_limit    = var.snapshot_retention_limit
  snapshot_window             = var.backup_window
  subnet_group_name           = var.redis_subnet_group_name
  transit_encryption_enabled  = true
  apply_immediately           = true
  log_delivery_configuration {
    destination      = module.redis_log_group.name
    destination_type = "cloudwatch-logs"
    log_format       = "json"
    log_type         = "slow-log"
  }
}

module "redis_log_group" {
  source             = "../../modules/encrypted_log_group"
  log_group_name     = "${var.environment_name}-redis"
  log_retention_days = var.cloudwatch_log_expiration_days
}


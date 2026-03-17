output "redis_security_group_id" {
  value       = aws_security_group.redis.id
  description = "ID for the security group for redis"
}

output "redis_cluster_ids" {
  value       = aws_elasticache_replication_group.main.member_clusters
  description = "IDs of the redis clusters"
}
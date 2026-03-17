output "ecs_cluster_arn" {
  value       = aws_ecs_cluster.main.arn
  description = "The arn of the ecs cluster for this environment"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "The name of the ECS cluster for this environment"
}

output "ecs_service_arn" {
  value       = aws_ecs_service.webapp.id
  description = "The ARN of the ECS service for the web application"
}

output "ecs_service_name" {
  value       = aws_ecs_service.webapp.name
  description = "The name of the ECS service for the web application"
}

output "ecs_security_group_ids" {
  value       = [aws_security_group.ecs.id]
  description = "List of security group IDs attached to the ECS tasks"
}
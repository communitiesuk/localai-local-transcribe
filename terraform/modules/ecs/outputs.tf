output "ecs_cluster_arn" {
  value       = aws_ecs_cluster.main.arn
  description = "The arn of the ecs cluster for this environment"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "The name of the ECS cluster for this environment"
}

output "backend_execution_task_name" {
  value       = aws_iam_role.ecs_task_execution.name
  description = "The name of the task execution role used by the backend ecs task"
}

output "worker_execution_task_name" {
  value       = aws_iam_role.ecs_task_execution.name
  description = "The name of the task execution role used by the worker ecs task"
}

output "frontend_execution_task_id" {
  value       = aws_iam_role.ecs_task_execution.id
  description = "The id of the task execution role used by the frontend ecs task"
}

output "backend_execution_task_id" {
  value       = aws_iam_role.ecs_task_execution.id
  description = "The id of the task execution role used by the backend ecs task"
}

output "worker_execution_task_id" {
  value       = aws_iam_role.ecs_task_execution.id
  description = "The id of the task execution role used by the worker ecs task"
}

output "frontend_execution_task_arn" {
  value       = aws_iam_role.ecs_task_execution.arn
  description = "The arn of the task execution role used by the frontend ecs task"
}

output "backend_execution_task_arn" {
  value       = aws_iam_role.ecs_task_execution.arn
  description = "The arn of the task execution role used by the backend ecs task"
}

output "worker_execution_task_arn" {
  value       = aws_iam_role.ecs_task_execution.arn
  description = "The arn of the task execution role used by the worker ecs task"
}

output "backend_task_role_name" {
  value       = aws_iam_role.backend_ecs_task.name
  description = "The name of the task role used by the backend ecs task"
}

output "worker_task_role_name" {
  value       = aws_iam_role.worker_ecs_task.name
  description = "The name of the task role used by the worker ecs task"
}

output "frontend_service_name" {
  description = "The name of the frontend ecs service"
  value       = aws_ecs_service.frontend.name
}

output "backend_service_name" {
  description = "The name of the backend ecs service"
  value       = aws_ecs_service.backend.name
}

output "worker_service_name" {
  description = "The name of the worker ecs service"
  value       = aws_ecs_service.worker.name
}

output "backend_log_group_name" {
  description = "CloudWatch log group name for backend ECS service logs"
  value       = module.backend_log_group.name
}

output "worker_log_group_name" {
  description = "CloudWatch log group name for worker ECS service logs"
  value       = module.worker_log_group.name
}
variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "webapp_task_execution_role_name" {
  description = "Name of the IAM role for the webapp ECS task execution"
  type        = string
}

variable "ecs_cluster_arn" {
  description = "ARN of the ECS cluster where the webapp service will run"
  type        = string
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs where the ECS tasks will run"
}

variable "ecs_security_group_ids" {
  type        = list(string)
  description = "List of security group IDs to attach to the ECS tasks"
}
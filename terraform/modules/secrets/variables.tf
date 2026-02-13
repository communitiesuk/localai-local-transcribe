variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "webapp_task_execution_role_arn" {
  description = "ARN of the IAM role for the webapp ECS task execution"
  type        = string
}

variable "webapp_task_execution_role_id" {
  description = "ID of the IAM role for the webapp ECS task execution"
  type        = string
}
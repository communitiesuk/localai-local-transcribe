variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "backend_task_execution_role_name" {
  description = "Name of the IAM role for the backend ECS task execution"
  type        = string
}

variable "worker_task_execution_role_name" {
  description = "Name of the IAM role for the worker ECS task execution"
  type        = string
}

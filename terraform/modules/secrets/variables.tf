variable "environment_name" {
  description = "must be one of: integration, test, staging, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "frontend_task_execution_role_arn" {
  description = "ARN of the IAM role for the frontend ECS task execution"
  type        = string
}

variable "backend_task_execution_role_arn" {
  description = "ARN of the IAM role for the backend ECS task execution"
  type        = string
}

variable "worker_task_execution_role_arn" {
  description = "ARN of the IAM role for the worker ECS task execution"
  type        = string
}

variable "frontend_task_execution_role_id" {
  description = "id of the IAM role for the frontend ECS task execution"
  type        = string
}

variable "backend_task_execution_role_id" {
  description = "id of the IAM role for the backend ECS task execution"
  type        = string
}

variable "worker_task_execution_role_id" {
  description = "id of the IAM role for the worker ECS task execution"
  type        = string
}
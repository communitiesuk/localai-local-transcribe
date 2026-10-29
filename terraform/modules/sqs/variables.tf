variable "environment_name" {
  description = "must be one of: development, staging, or production"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "backend_task_role_name" {
  description = "Name of the IAM task role for the backend ECS task"
  type        = string
}

variable "worker_task_role_name" {
  description = "Name of the IAM task role for the worker ECS task"
  type        = string
}

variable "environment_name" {
  description = "must be one of: development, or staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
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

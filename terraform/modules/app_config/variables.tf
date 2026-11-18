
variable "environment_name" {
  description = "must be one of: development, staging, or production"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "backend_task_role_name" {
  description = "Name of the backend ECS task role that should be granted permission to read this AppConfig configuration"
  type        = string
}
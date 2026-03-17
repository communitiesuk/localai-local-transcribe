variable "environment_name" {
  description = "Environment name (e.g., integration, test, production)"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test, nft, or production"
  }
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs where ECS tasks will run"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to scheduled tasks"
  type        = list(string)
  default     = []
}

variable "schedule_expressions" {
  description = "Map of scheduled tasks with their configurations"
  type = map(object({
    schedule_expression = string
  }))
}

variable "task_role_arn" {
  description = "ARN of the IAM role that scheduled tasks will assume"
  type        = string
}

variable "task_execution_role_arn" {
  description = "ARN of the IAM role that scheduled tasks will use for execution"
  type        = string
}

variable "alarm_email_address" {
  description = "Email address to send alarms to"
  type        = string
}
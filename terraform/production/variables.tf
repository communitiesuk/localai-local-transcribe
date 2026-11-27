variable "ssl_certs_created" {
  description = "Indicates whether ssl certificates have already been manually created"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "The image tag to be used for all of frontend, backend, and worker"
  type        = string
  default     = "latest"
}

variable "alarm_email_address" {
  description = "Deprecated: Email address to receive CloudWatch alarm notifications"
  type        = string
  sensitive   = true
  default     = null
}

variable "alarm_email_addresses" {
  description = "Email addresses to receive CloudWatch alarm notifications, map of non-sensitive identifier to email address"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "maintenance_mode_on" {
  description = "Enable maintenance mode"
  type        = bool
  default     = false
}

variable "frontend_task_memory" {
  description = "Memory for the frontend ECS task definition - prod"
  type        = number
  default     = 2048
}

variable "backend_task_memory" {
  description = "Memory for the backend ECS task definition - prod"
  type        = number
  default     = 8192
}

variable "worker_task_memory" {
  description = "Memory for the worker ECS task definition - prod"
  type        = number
  default     = 8192
}

variable "frontend_task_cpu" {
  description = "CPU units for the frontend ECS task definition"
  type        = number
  default     = 1024
}

variable "backend_task_cpu" {
  description = "CPU units for the backend ECS task definition"
  type        = number
  default     = 4096
}

variable "worker_task_cpu" {
  description = "CPU units for the worker ECS task definition"
  type        = number
  default     = 4096
}

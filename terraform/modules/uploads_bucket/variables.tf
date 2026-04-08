variable "environment_name" {
  description = "must be one of: development, or staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
  }
}

variable "force_destroy" {
  description = "Whether to force destroy the bucket when it contains objects. This should be set to true for non-production environments to avoid issues with leftover objects preventing bucket deletion."
  type        = string
  validation {
    condition     = contains(["true", "false"], var.force_destroy)
    error_message = "force_destroy must be either 'true' or 'false'"
  }
}

variable "kms_key" {
  description = "Optional. KMS key to encrypt bucket and access logs bucket."
  type        = string
  default     = null
}

variable "access_s3_log_expiration_days" {
  description = "The number of days to retain s3 access logs"
  type        = number
}

variable "app_host" {
  description = "Application url"
  type        = string
}

variable "worker_task_role_name" {
  description = "Name of the IAM role for the worker ECS task"
  type        = string
}

variable "backend_task_role_name" {
  description = "Name of the IAM role for the backend ECS task"
  type        = string
}

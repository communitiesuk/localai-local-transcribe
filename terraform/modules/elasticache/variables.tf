variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "redis_password" {
  description = "password for elasticache"
  type        = string
  sensitive   = true
}

variable "highly_available" {
  type        = bool
  description = "Whether or not to make redis highly available (whether to have replicas or not)."
}

variable "node_type" {
  type        = string
  description = "The type of node for the redis elasticache."
}

variable "redis_port" {
  type        = number
  description = "The network port redis runs on"
}

variable "redis_subnet_group_name" {
  type        = string
  description = "The name of the subnet group associated with the VPC that redis needs to be in."
}

variable "snapshot_retention_limit" {
  type        = number
  description = "The number of days the automatic cache cluster snapshots are retained before being deleted. If 0 then backups are turned off"
}

variable "backup_window" {
  type        = string
  description = "Backup window for redis."
  default     = "02:30-03:30"
}

variable "maintenance_window" {
  type        = string
  description = "Maintenance window for redis."
  default     = "sun:23:00-mon:01:30"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC to be associated with"
}

variable "cloudwatch_log_expiration_days" {
  type        = number
  description = "Number of days to retain cloudwatch logs for"
}

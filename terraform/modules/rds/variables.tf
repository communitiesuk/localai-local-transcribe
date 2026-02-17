variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "database_password" {
  description = "password for the database"
  type        = string
  sensitive   = true
}

variable "database_port" {
  description = "port for the database"
  type        = number
}

variable "allocated_storage" {
  type        = number
  description = "The allocated DB storage in gibibytes."
}

variable "backup_retention_period" {
  type        = number
  description = "The number of days to retain db backups for. If 0 then the database will not be backed up"
}

variable "backup_window" {
  type        = string
  description = "Backup window for the db."
  default     = "23:09-23:39"
}

variable "db_subnet_group_name" {
  type        = string
  description = "The name of the subnet group associated with the VPC the DB needs to be in."
}

variable "instance_class" {
  type        = string
  description = "The instance class of the DB."
}

variable "maintenance_window" {
  type        = string
  description = "Maintenance window for the db."
  default     = "Mon:02:33-Mon:03:03"
}

variable "multi_az" {
  type        = bool
  description = "Whether the database should be multi-az"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC to be associated with"
}

variable "webapp_task_execution_role_name" {
  description = "Name of the IAM role for the webapp ECS task execution"
  type        = string
}
variable "bastion_group_id" {
  type        = string
  description = "The id of the bastion security group"
}
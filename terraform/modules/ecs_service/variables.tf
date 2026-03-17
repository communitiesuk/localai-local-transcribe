variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "webapp_task_desired_count" {
  description = "target number of tasks to deploy"
  type        = number
}

variable "allow_exec" {
  description = "whether to enable AWS ECS Exec on the instance"
  type        = bool
  default     = true
}

variable "application_port" {
  description = "The network port the application runs on"
  type        = number
}

variable "database_port" {
  description = "The port for the database"
  type        = number
}

variable "redis_port" {
  description = "The port used by elasticache"
  type        = number
}

variable "lb_target_group_arn" {
  description = "ARN of the main load balancer target group"
  type        = string
}

variable "lb_security_group_id" {
  description = "id of the load balancer security group"
  type        = string
}

variable "db_security_group_id" {
  description = "id of the database security group"
  type        = string
}

variable "redis_security_group_id" {
  description = "id of the redis security group"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of subnet ids to deploy the task to"
  type        = list(string)
}

variable "vpc_id" {
  description = "id of the VPC"
  type        = string
}

variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test, nft, or production"
  }
}

variable "alarm_email_address" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
}

variable "cloudwatch_log_expiration_days" {
  type        = number
  description = "Number of days to retain cloudwatch logs for"
}

variable "ecs_cluster_name" {
  description = "Name of ECS cluster to create alarms for"
  type        = string
}

variable "ecs_service_name" {
  description = "Name of ECS service to create alarms for"
  type        = string
}

variable "database_identifier" {
  description = "Identifier of DB instance to create alarms for"
  type        = string
}

variable "database_allocated_storage" {
  description = "Allocated storage of RDS instance to create alarms for"
  type        = number
}

variable "elasticache_cluster_ids" {
  description = "IDs of ElastiCache clusters to create alarms for"
  type        = set(string)
}

variable "alb_name" {
  description = "Name of ALB to create alarms for"
  type        = string
}

variable "alb_arn_suffix" {
  description = "ARN suffix of ALB to create alarms for"
  type        = string
}

variable "alb_target_group_arn_suffix" {
  description = "ARN suffix of target group of ALB to create alarms for"
  type        = string
}

variable "waf_acl_name" {
  description = "Name of WAF web ACL to create alarms for"
  type        = string
}
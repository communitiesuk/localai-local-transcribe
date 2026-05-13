variable "environment_name" {
  description = "must be one of: development, or staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
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

variable "ecs_cluster_arn" {
  description = "Arn of ECS cluster to create alarms for"
  type = string
}

variable "ecs_service_names" {
  description = "Names of ECS service to create alarms for"
  type        = list(string)
}

variable "database_identifier" {
  description = "Identifier of DB instance to create alarms for"
  type        = string
}

variable "database_allocated_storage" {
  description = "Allocated storage of RDS instance to create alarms for"
  type        = number
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

variable "transcription_deadletter_queue_name" {
  description = "Name of the SQS queue for transcriptions, to create alarms for"
  type        = string
}

variable "llm_deadletter_queue_name" {
  description = "Name of the SQS queue for LLM processing, to create alarms for"
  type        = string
}
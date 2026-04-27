variable "log_group_name" {
  description = "cloudwatch log group name"
  type        = string
}

variable "log_retention_days" {
  description = "cloudwatch log retention period in days"
  type        = number
}

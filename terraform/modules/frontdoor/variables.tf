variable "ssl_certs_created" {
  description = "Indicates whether ssl certificates have already been manually created"
  type        = bool
}

variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "The ids of all the public subnets"
}

variable "cloudfront_certificate_arn" {
  type        = string
  description = "The arn of the certificate to be associated with the cloudfront distribution"
  default     = null
}

variable "load_balancer_certificate_arn" {
  type        = string
  description = "The arn of the certificate to be associated with the load balancer HTTPS listener"
  default     = null
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC to be associated with."
}

variable "application_port" {
  type        = number
  description = "The network port the application runs on"
}

# TODO: PRSD-574 - Reinstate when ECS has been configured
# variable "ecs_security_group_id" {
#   type        = string
#   description = "The id of the ecs security group for ecs egress"
# }

variable "cloudfront_domain_names" {
  type        = list(string)
  description = "All MHCLG delegated domain names for cloudfront"
}

variable "load_balancer_domain_name" {
  type        = string
  description = "MHCLG delegated domain name for alb"
}

variable "geolocation_allow_list" {
  type        = list(string)
  description = "List of allowed locations - geo restrictions disabled when set to null"
  default     = null
}

variable "ip_allowlist" {
  type        = list(string)
  description = "List of allowed IPs - if empty then no ip restrictions are applied"
  default     = []
}

variable "cloudwatch_log_expiration_days" {
  type        = number
  description = "Number of days to retain cloudwatch logs for"
}

variable "use_aws_shield_advanced" {
  type        = bool
  description = "Indicates whether AWS Shield Advanced should be enabled"
}

variable "maintenance_mode_on" {
  type        = bool
  description = "Indicates whether maintenance mode is on"
  default     = false
}
variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "vpc_cidr_block" {
  type        = string
  description = "A collection of IP addresses to be allocated to VPC."
}

variable "number_of_availability_zones" {
  default     = 2
  type        = number
  description = "Number of availability zones we will deploy to; must be 2 <= x <= number of available AZs"
}

variable "number_of_isolated_subnets" {
  default     = 1
  type        = number
  description = "Each isolated subnet is located in a different AZ; must be 1 <= x <= number of available AZs"
}

variable "vpc_flow_cloudwatch_log_expiration_days" {
  type        = number
  description = "Number of days to retain VPC flow logs for"
}

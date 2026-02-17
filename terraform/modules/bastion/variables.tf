variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "main_vpc_id" {
  type        = string
  description = "The id of the VPC."
}

variable "vpc_cidr_block" {
  type        = string
  description = "A collection of IP addresses to be allocated to VPC."
}

variable "bastion_subnet_ids" {
  type        = list(string)
  description = "The private subnets into which to deploy a bastion"
}

variable "bastion_ssm_patch_cloudwatch_log_expiration_days" {
  type        = number
  description = "Number of days to retain SSM bastion patch logs for"
}
variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "landlord_base_url" {
  description = "base URL for the landlord service"
  type        = string
}

variable "local_council_base_url" {
  description = "base URL for the local council service"
  type        = string
}

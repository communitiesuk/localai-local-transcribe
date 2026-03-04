variable "environment_name" {
  description = "must be one of: integration, test, staging, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "image_retention_count" {
  description = "the number of images to retain"
  type        = number
}
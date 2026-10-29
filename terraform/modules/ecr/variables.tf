variable "environment_name" {
  description = "must be one of: development, staging, or production"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "image_retention_count" {
  description = "the number of images to retain"
  type        = number
}
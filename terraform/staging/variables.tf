variable "ssl_certs_created" {
  description = "Indicates whether ssl certificates have already been manually created"
  type        = bool
  default     = true
}

variable "image_tag" {
  description = "The image tag to be used for all of frontend, backend, and worker"
  type        = string
  default     = "latest"
}

variable "alarm_email_address" {
  description = "Deprecated: Email address to receive CloudWatch alarm notifications"
  type        = string
  sensitive   = true
  default     = null
}

variable "alarm_email_addresses" {
  description = "Email addresses to receive CloudWatch alarm notifications, map of non-sensitive identifier to email address"
  type        = map(string)
  sensitive   = true
  default     = {}
}

variable "maintenance_mode_on" {
  description = "Enable maintenance mode"
  type        = bool
  default     = false
}

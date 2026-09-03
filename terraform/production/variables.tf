variable "ssl_certs_created" {
  description = "Indicates whether ssl certificates have already been manually created"
  type        = bool
  default     = false
}

variable "image_tag" {
  description = "The image tag to be used for all of frontend, backend, and worker"
  type        = string
  default     = "latest"
}

variable "alarm_email_address" {
  description = "Email address to receive CloudWatch alarm notifications"
  type        = string
  sensitive   = true
}

variable "maintenance_mode_on" {
  description = "Enable maintenance mode"
  type        = bool
  default     = false
}

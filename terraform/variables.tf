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
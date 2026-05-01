variable "cloudfront_domain_name" {
  type        = string
  description = "The domain name of the cloudfront distribution"
}

variable "cloudfront_additional_names" {
  type        = list(string)
  description = "Additional names to add to the cloudfront certificate"
  default     = []
}

variable "load_balancer_domain_name" {
  type        = string
  description = "The domain name of the load balancer"
}

variable "load_balancer_additional_names" {
  type        = list(string)
  description = "Additional names to add to the load balancer certificate"
  default     = []
}
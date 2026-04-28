resource "aws_acm_certificate" "cloudfront" {
  domain_name       = var.cloudfront_domain_name
  validation_method = "DNS"

  subject_alternative_names = var.cloudfront_additional_names

  # Cloudfront certs must be in US East 1
  provider = aws.us-east-1

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_acm_certificate" "load_balancer" {
  domain_name       = var.load_balancer_domain_name
  validation_method = "DNS"

  subject_alternative_names = var.load_balancer_additional_names

  lifecycle {
    create_before_destroy = true
  }
}
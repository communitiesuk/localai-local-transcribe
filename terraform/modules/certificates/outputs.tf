output "cloudfront_certificate_arn" {
  value       = aws_acm_certificate.cloudfront.arn
  description = "The arn of the cloudfront certificate"
}

output "cloudfront_certificate_validation" {
  value       = aws_acm_certificate.cloudfront.domain_validation_options
  description = "The domain validation objects for the cloudfront certificate"
}

output "load_balancer_certificate_arn" {
  value       = aws_acm_certificate.load_balancer.arn
  description = "The arn of the load balancer certificate"
}

output "load_balancer_certificate_validation" {
  value       = aws_acm_certificate.load_balancer.domain_validation_options
  description = "The domain validation objects for the load balancer certificate"
}
output "public_subnet_ids" {
  value       = module.networking.public_subnets[*].id
  description = "The ids of the public subnets"
}

output "vpc_id" {
  value       = module.networking.vpc.id
  description = "The id of the vpc"
}

output "load_balancer_dns_name" {
  value       = module.frontdoor.load_balancer.dns_name
  description = "The domain name of the application load balancer"
}

output "cloudfront_dns_name" {
  value       = module.frontdoor.cloudfront_dns_name
  description = "The domain name of the cloudfront distribution"
}

output "cloudfront_certificate_validation" {
  value       = module.certificates.cloudfront_certificate_validation
  description = "The domain validation objects for the cloudfront certificate"
}

output "load_balancer_certificate_validation" {
  value       = module.certificates.load_balancer_certificate_validation
  description = "The domain validation objects for the load balancer certificate"
}

output "ecr_repository_url" {
  value       = module.ecr.ecr_repository_url
  description = "The url of the ecr repository for this environment"
}
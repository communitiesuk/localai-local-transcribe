terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
  }

  backend "s3" {
    bucket         = "minute-tfstate"
    dynamodb_table = "tfstate-lock"
    encrypt        = true
    key            = "minute-infra-prod" #TODO: how do we split different environments?
    region         = "eu-west-2"
  }
}

locals {
  environment_name = "production"

  frontend_port = 3000
  backend_port  = 8080

  app_host                  = "minute.communities.gov.uk"    # Placeholder
  load_balancer_domain_name = "lb.minute.communities.gov.uk" # Placeholder

  cloudwatch_log_exipiration_days = 90
}

provider "aws" {
  region = "eu-west-2"
}

provider "aws" {
  alias  = "us-east-1"
  region = "us-east-1"
}

module "networking" {
  source                       = "./modules/networking"
  vpc_cidr_block               = "10.1.0.0/16"
  environment_name             = local.environment_name
  number_of_availability_zones = 2
  number_of_isolated_subnets   = 2 # RDS requires there to be 2 subnets in different AZs even when multi-AZ is disabled

  vpc_flow_cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
}

module "frontdoor" {
  source = "./modules/frontdoor"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  ssl_certs_created = var.ssl_certs_created
  environment_name  = local.environment_name
  public_subnet_ids = module.networking.public_subnets[*].id
  vpc_id            = module.networking.vpc.id
  application_port  = local.frontend_port
  cloudfront_domain_names = [
    local.app_host,
  ]
  load_balancer_domain_name      = local.load_balancer_domain_name
  cloudfront_certificate_arn     = module.certificates.cloudfront_certificate_arn
  load_balancer_certificate_arn  = module.certificates.load_balancer_certificate_arn
  cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
  use_aws_shield_advanced        = true
}

module "certificates" {
  source = "./modules/certificates"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  cloudfront_domain_name    = local.app_host
  load_balancer_domain_name = local.load_balancer_domain_name
}

module "ecr" {
  source = "./modules/ecr"

  environment_name = local.environment_name
  image_retention_count = 10
}
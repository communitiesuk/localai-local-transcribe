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
  multi_az         = false

  frontend_port = 3000
  backend_port  = 8080
  database_port = 5432

  app_host                  = "minute.communities.gov.uk"    # Placeholder
  load_balancer_domain_name = "lb.minute.communities.gov.uk" # Placeholder

  cloudwatch_log_exipiration_days = 90
  database_allocated_storage      = 50
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

  environment_name      = local.environment_name
  image_retention_count = 10
}

module "secrets" {
  source = "./modules/secrets"

  environment_name               = local.environment_name
  webapp_task_execution_role_arn = module.ecr.ecs_task_execution_role_arn
  webapp_task_execution_role_id  = module.ecr.ecs_task_execution_role_id
}

module "bastion" {
  source = "./modules/bastion"

  bastion_subnet_ids = module.networking.private_subnets[*].id
  environment_name   = local.environment_name
  main_vpc_id        = module.networking.vpc.id
  vpc_cidr_block     = module.networking.vpc.cidr_block

  bastion_ssm_patch_cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
}

module "database" {
  source = "./modules/rds"

  environment_name = local.environment_name
  database_password               = module.secrets.database_password.result
  database_port                   = local.database_port
  allocated_storage               = local.database_allocated_storage
  backup_retention_period         = 7
  db_subnet_group_name            = module.networking.db_subnet_group_name
  instance_class                  = "db.t4g.small"
  multi_az                        = local.multi_az
  vpc_id                          = module.networking.vpc.id
  webapp_task_execution_role_name = module.ecr.webapp_ecs_task_role_name
  bastion_group_id                = module.bastion.security_group_id
}
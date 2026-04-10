terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
  }

  backend "s3" {
    bucket       = "local-transcribe-tfstate-development"
    use_lockfile = true
    encrypt      = true
    key          = "local-transcribe-infra-development"
    region       = "eu-west-2"
  }
}

locals {
  environment_name = "development"
  aws_region       = "eu-west-2"
  multi_az         = false

  frontend_port               = 3000
  backend_port                = 8080
  database_port               = 5432
  max_transcription_processes = 1
  max_llm_proccesses          = 1

  database_username = "postgres"

  app_host                  = "development.local-transcribe.test.communities.gov.uk"    # placeholder
  load_balancer_domain_name = "lb.development.local-transcribe.test.communities.gov.uk" # placeholder

  cloudwatch_log_exipiration_days = 90
  access_s3_log_expiration_days   = 90
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
  source                       = "../modules/networking"
  vpc_cidr_block               = "10.1.0.0/16"
  environment_name             = local.environment_name
  number_of_availability_zones = 2
  number_of_isolated_subnets   = 2 # RDS requires there to be 2 subnets in different AZs even when multi-AZ is disabled

  vpc_flow_cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
}

module "frontdoor" {
  source = "../modules/frontdoor"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  ssl_certs_created = var.ssl_certs_created
  environment_name  = local.environment_name
  public_subnet_ids = module.networking.public_subnets[*].id
  vpc_id            = module.networking.vpc.id
  frontend_port     = local.frontend_port
  cloudfront_domain_names = [
    local.app_host,
  ]
  load_balancer_domain_name      = local.load_balancer_domain_name
  cloudfront_certificate_arn     = module.certificates.cloudfront_certificate_arn
  load_balancer_certificate_arn  = module.certificates.load_balancer_certificate_arn
  cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days

  use_aws_shield_advanced        = false
  enable_oidc_auth               = false
  ip_allowlist = [
    # Softwire
    "31.221.86.178/32",
    "167.98.33.82/32",
    "87.224.105.250/32",
    "87.224.116.242/32",
    "45.150.142.210/32",
    # MHCLG
    "4.158.35.41/32",
  ]

  app_host                       = local.app_host
  oidc_client_id_name            = module.secrets.oidc_client_id_name
  oidc_client_secret_name        = module.secrets.oidc_client_secret_name
}

module "certificates" {
  source = "../modules/certificates"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  cloudfront_domain_name    = local.app_host
  load_balancer_domain_name = local.load_balancer_domain_name
}

module "ecr" {
  source = "../modules/ecr"

  environment_name      = local.environment_name
  image_retention_count = 10
}

module "secrets" {
  source = "../modules/secrets"

  environment_name = local.environment_name

  frontend_task_execution_role_arn = module.ecs.frontend_execution_task_arn
  frontend_task_execution_role_id  = module.ecs.frontend_execution_task_id
  backend_task_execution_role_arn  = module.ecs.backend_execution_task_arn
  backend_task_execution_role_id   = module.ecs.backend_execution_task_id
  worker_task_execution_role_arn   = module.ecs.worker_execution_task_arn
  worker_task_execution_role_id    = module.ecs.worker_execution_task_id
}

module "bastion" {
  source = "../modules/bastion"

  bastion_subnet_ids = module.networking.private_subnets[*].id
  environment_name   = local.environment_name
  main_vpc_id        = module.networking.vpc.id
  vpc_cidr_block     = module.networking.vpc.cidr_block

  bastion_ssm_patch_cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
}

module "database" {
  source = "../modules/rds"

  environment_name                 = local.environment_name
  database_username                = local.database_username
  database_password                = module.secrets.database_password.result
  database_port                    = local.database_port
  allocated_storage                = local.database_allocated_storage
  backup_retention_period          = 7
  db_subnet_group_name             = module.networking.db_subnet_group_name
  instance_class                   = "db.t4g.small"
  multi_az                         = local.multi_az
  vpc_id                           = module.networking.vpc.id
  backend_task_execution_role_name = module.ecs.backend_execution_task_name
  worker_task_execution_role_name  = module.ecs.worker_execution_task_name
  bastion_group_id                 = module.bastion.security_group_id
}

module "sqs" {
  source           = "../modules/sqs"
  environment_name = local.environment_name

  worker_task_role_name  = module.ecs.worker_task_role_name
  backend_task_role_name = module.ecs.backend_task_role_name
}

module "ecs" {
  source = "../modules/ecs"

  environment_name            = local.environment_name
  frontend_task_desired_count = 1
  backend_task_desired_count  = 1
  worker_task_desired_count   = 1
  frontend_port               = local.frontend_port
  backend_port                = local.backend_port

  database_port     = local.database_port
  database_host     = module.database.database_url
  database_name     = module.database.database_name
  database_user     = local.database_username
  database_password = module.secrets.database_password.result

  lb_target_group_arn  = module.frontdoor.load_balancer.target_group_arn
  lb_security_group_id = module.frontdoor.load_balancer.security_group_id
  db_security_group_id = module.database.rds_security_group_id
  bastion_sg_id        = module.bastion.security_group_id
  environment          = "local" # Set to local to bypass authentication
  data_s3_bucket_name  = module.uploads_bucket.bucket_name
  private_subnet_ids   = module.networking.private_subnets[*].id
  vpc_id               = module.networking.vpc.id
  app_url              = local.app_host

  frontend_image_name = "${module.ecr.ecr_frontend_repository_url}:${var.image_tag}"
  backend_image_name  = "${module.ecr.ecr_backend_repository_url}:${var.image_tag}"
  worker_image_name   = "${module.ecr.ecr_worker_repository_url}:${var.image_tag}"

  llm_queue_name                      = module.sqs.llm_queue_name
  llm_deadletter_queue_name           = module.sqs.llm_deadletter_queue_name
  transcription_queue_name            = module.sqs.transcription_queue_name
  transcription_deadletter_queue_name = module.sqs.transcription_deadletter_queue_name

  max_llm_processes           = local.max_llm_proccesses
  max_transcription_processes = local.max_transcription_processes
  alb_arn                     = module.frontdoor.load_balancer.arn
  oidc_issuer                 = module.frontdoor.oidc_issuer
  aws_region                  = local.aws_region
  lb_listener_exists          = var.ssl_certs_created

  azure_speech_key_arn    = module.secrets.azure_speech_key_arn
  azure_speech_region_arn = module.secrets.azure_speech_region_arn
}

module "uploads_bucket" {
  source = "../modules/uploads_bucket"

  app_host                        = local.app_host
  environment_name                = local.environment_name
  access_s3_log_expiration_days   = local.access_s3_log_expiration_days
  force_destroy                   = false
  worker_task_role_name = module.ecs.worker_task_role_name
  backend_task_role_name          = module.ecs.backend_task_role_name
}

module "monitoring" {
  source = "../modules/monitoring"

  providers = {
    aws.us-east-1 = aws.us-east-1
  }

  environment_name                    = local.environment_name
  cloudwatch_log_expiration_days      = local.cloudwatch_log_exipiration_days
  alarm_email_address                 = var.alarm_email_address
  alb_name                            = module.frontdoor.load_balancer.name
  alb_arn_suffix                      = module.frontdoor.load_balancer.arn_suffix
  alb_target_group_arn_suffix         = module.frontdoor.load_balancer.arn_suffix
  ecs_cluster_name                    = module.ecs.ecs_cluster_name
  ecs_service_names                   = [module.ecs.frontend_service_name, module.ecs.backend_service_name, module.ecs.worker_service_name]
  database_allocated_storage          = local.database_allocated_storage
  database_identifier                 = module.database.database_identifier
  waf_acl_name                        = module.frontdoor.waf_acl_name
  llm_deadletter_queue_name           = module.sqs.llm_deadletter_queue_name
  transcription_deadletter_queue_name = module.sqs.transcription_deadletter_queue_name
}
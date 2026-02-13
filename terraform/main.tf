terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
  }

  backend "s3" {
    bucket = "minute-tfstate"
    dynamodb_table = "tfstate-lock"
    encrypt = true
    key = "minute-infra-prod" #TODO: how do we split different environments?
    region = "eu-west-2"
  }
}

locals {
  environment_name = "production"

  cloudwatch_log_exipiration_days = 90
}

provider "aws" {
  region = "eu-west-2"
}

module "networking" {
  source = "./modules/networking"
  vpc_cidr_block = "10.1.0.0/16"
  environment_name = local.environment_name
  number_of_availability_zones = 2
  number_of_isolated_subnets = 2 # RDS requires there to be 2 subnets in different AZs even when multi-AZ is disabled

  vpc_flow_cloudwatch_log_expiration_days = local.cloudwatch_log_exipiration_days
}
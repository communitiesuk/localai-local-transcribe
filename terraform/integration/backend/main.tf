terraform {
  required_version = "~>1.9.1"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>5.0"
    }
  }

  backend "s3" {
    bucket         = "prsdb-tfstate-integration"
    dynamodb_table = "tfstate-lock-integration"
    encrypt        = true
    key            = "prsdb-infra-integration-tfstate"
    region         = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
}

module "terraform_backend" {
  source           = "../../modules/terraform_backend"
  environment_name = "integration"
}
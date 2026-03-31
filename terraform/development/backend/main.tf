terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
  }

  backend "s3" {
    bucket         = "local-transcribe-tfstate-dev"
    dynamodb_table = "tfstate-lock-dev"
    encrypt        = true
    key            = "local-transcribe-infra-dev-tfstate"
    region         = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
}

module "terraform_backend" {
  source           = "../../modules/terraform_backend"
  environment_name = "dev"
}
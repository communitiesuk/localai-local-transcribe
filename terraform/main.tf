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

provider "aws" {
  region = "eu-west-2"
}
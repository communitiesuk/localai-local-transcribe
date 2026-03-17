terraform {
  required_version = "~>1.9.1"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~>5.0"
      configuration_aliases = [aws.us-east-1]
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~>6.5"
      configuration_aliases = [aws.us-east-1]
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
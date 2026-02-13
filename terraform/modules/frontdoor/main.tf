locals {
  cloudfront_header_name = "X-CLOUDFRONT-HEADER"
}

terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~>6.5"
      configuration_aliases = [aws.us-east-1]
    }
    random = {
      version = "~>3.5"
      source  = "hashicorp/random"
    }
  }
}

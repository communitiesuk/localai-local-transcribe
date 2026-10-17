locals {
  cloudfront_header_name             = "X-CLOUDFRONT-HEADER"
  waf_body_size_exception_path_regex = "^(/monitoring|/api/proxy/minutes/[A-Fa-f0-9]{8}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{4}-[A-Fa-f0-9]{12}/versions)/?$"
}

terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source                = "hashicorp/aws"
      configuration_aliases = [aws.us-east-1]
    }
    random = {
      version = "~>3.5"
      source  = "hashicorp/random"
    }
  }
}

terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "2.7.1"
    }
  }
}

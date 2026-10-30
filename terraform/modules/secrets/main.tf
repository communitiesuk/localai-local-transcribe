terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }
    random = {
      version = "~>3.5"
      source  = "hashicorp/random"
    }
  }
}

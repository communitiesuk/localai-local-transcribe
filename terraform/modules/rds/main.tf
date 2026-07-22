terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~>6.5"
    }

    postgresql = {
      source  = "cyrilgdn/postgresql"
      version = "~>1.26"
    }
  }
}
terraform {
  required_version = "~>1.14.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Pinned: 6.57.0 breaks reads of SSM parameters, IAM policies and IAM OIDC
      # providers (SerializationException). Unpin once a fix is released.
      # https://github.com/hashicorp/terraform-provider-aws/issues/49170
      version = "6.56.0"
    }
  }

  backend "s3" {
    bucket       = "local-transcribe-tfstate-staging"
    use_lockfile = true
    encrypt      = true
    key          = "local-transcribe-state-infra-staging"
    region       = "eu-west-2"
  }
}

provider "aws" {
  region = "eu-west-2"
}

module "terraform_backend" {
  source           = "../../modules/terraform_backend"
  environment_name = "staging"
}

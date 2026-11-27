variable "environment_name" {
  description = "must be one of: development, staging, or production"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.environment_name)
    error_message = "Environment must be one of: development, staging, production"
  }
}

variable "push_frontend_ecr_image_policy_arn" {
  description = "ARN of the IAM policy for pushing images to the frontend ECR repository"
  type        = string
}

variable "push_backend_ecr_image_policy_arn" {
  description = "ARN of the IAM policy for pushing images to the backend ECR repository"
  type        = string
}

variable "push_worker_ecr_image_policy_arn" {
  description = "ARN of the IAM policy for pushing images to the worker ECR repository"
  type        = string
}

variable "deployment_branch" {
  description = "Git branch that GitHub Actions may assume the deploy roles from. Must be one of: development, staging, or production"
  type        = string
  validation {
    condition     = contains(["development", "staging", "production"], var.deployment_branch)
    error_message = "Deployment branch must be one of: development, staging, production"
  }
}

variable "app_config_deploy_policy_arn" {
  description = "ARN of the IAM policy for deploying AppConfig feature flags"
  type        = string
}

variable "allow_plan_from_pull_requests" {
  description = "Let any pull request in this repository assume the Terraform plan role. A plan can read every secret in the environment's state, so this is only allowed in development"
  type        = bool
  default     = false
  validation {
    condition     = !var.allow_plan_from_pull_requests || var.environment_name == "development"
    error_message = "Pull requests may only assume the plan role in development. Use plan_github_environment for staging and production."
  }
}

variable "plan_github_environment" {
  description = "Name of a GitHub environment whose jobs may assume the Terraform plan role. The environment must have required reviewers, because approving a run lets it read every secret in this environment's state"
  type        = string
  default     = null
}

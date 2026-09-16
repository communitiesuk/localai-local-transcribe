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
  description = "Git branch that GitHub Actions may assume the deploy roles from"
  type        = string
  default     = "development"
}

variable "environment_name" {
  description = "must be one of: development, staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
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

variable "ecr_describe_images_policy_arn" {
  description = "arn of the iam policy for describing ecr images"
  type        = string
}

variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "push_ecr_image_policy_arn" {
  description = "arn of the iam policy for pushing images to ecr"
  type        = string
}

variable "db_username_ssm_parameter_arn" {
  description = "ARN of the SSM parameter that contains the database username"
  type        = string
}

variable "db_url_ssm_parameter_arn" {
  description = "ARN of the SSM parameter that contains the database URL"
  type        = string
}

variable "secrets_kms_key_arn" {
  description = "ARN of the KMS key used to encrypt the secrets"
  type        = string
}

variable "db_password_secret_arn" {
  description = "ARN of the Secrets Manager secret that contains the database password"
  type        = string
}

variable "bastion_host_arns" {
  description = "List of ARNs for the bastion host IAM roles that need access to GitHub Actions"
  type        = list(string)
  default     = []
}

variable "ecs_service_arn" {
  description = "ARN of the ECS service to restart"
  type        = string
}

variable "ecs_task_execution_role_arn" {
  description = "ARN of role used by ECS to execute tasks from the ecr repository"
  type        = string
}

variable "webapp_ecs_task_role_arn" {
  description = "ARN of role used by the webapp ECS task definition"
  type        = string
}

variable "task_definition_created" {
  description = "Boolean indicating if the ECS task definition has been created"
  type        = bool
  default     = true
}

variable "ecr_describe_images_policy_arn" {
  description = "arn of the iam policy for describing ecr images"
  type        = string
}
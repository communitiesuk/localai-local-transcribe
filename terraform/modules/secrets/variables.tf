variable "environment_name" {
  description = "must be one of: development, or staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
  }
}

variable "frontend_task_execution_role_arn" {
  description = "ARN of the IAM role for the frontend ECS task execution"
  type        = string
}

variable "backend_task_execution_role_arn" {
  description = "ARN of the IAM role for the backend ECS task execution"
  type        = string
}

variable "worker_task_execution_role_arn" {
  description = "ARN of the IAM role for the worker ECS task execution"
  type        = string
}

variable "frontend_task_execution_role_id" {
  description = "id of the IAM role for the frontend ECS task execution"
  type        = string
}

variable "backend_task_execution_role_id" {
  description = "id of the IAM role for the backend ECS task execution"
  type        = string
}

variable "worker_task_execution_role_id" {
  description = "id of the IAM role for the worker ECS task execution"
  type        = string
}

variable "database_username" {
  description = "username for the database"
  type        = string
  sensitive   = true
}

variable "database_port" {
  description = "port for the database"
  type        = number
}

variable "db_name" {
  description = "name of the database"
  type        = string
}

variable "database_url" {
  type        = string
  description = "the database host address"
}

variable "rotation_days" {
  type        = number
  description = "number of days between auto scheduled secret rotations"
  default     = 30
}

variable "master_user_secret_arn" {
  type        = string
  description = "the master user secret arn"
}

variable "vpc_id" {
  type        = string
  description = "The ID of the VPC to be associated with."
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of subnet ids to deploy the task to"
}

variable "lambda_rotation_sg_id" {
  type        = string
  description = " The ID of the security group attached to the Lambda secret-rotation function"
}

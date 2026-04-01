variable "environment_name" {
  description = "must be one of: development, or staging"
  type        = string
  validation {
    condition     = contains(["development", "staging"], var.environment_name)
    error_message = "Environment must be one of: development, staging"
  }
}

variable "frontend_task_desired_count" {
  description = "target number of frontend tasks to deploy"
  type        = number
}

variable "backend_task_desired_count" {
  description = "target number of backend tasks to deploy"
  type        = number
}

variable "worker_task_desired_count" {
  description = "target number of worker tasks to deploy"
  type        = number
}

variable "allow_exec" {
  description = "whether to enable AWS ECS Exec on the instance"
  type        = bool
  default     = true
}

variable "frontend_port" {
  description = "The network port the frontend runs on"
  type        = number
}

variable "backend_port" {
  description = "The network port the backend runs on"
  type        = number
}

variable "database_host" {
  description = "Database primary database host"
  type        = string
}

variable "database_port" {
  description = "The port for the database"
  type        = number
}

variable "database_user" {
  description = "Database username"
  type        = string
}

variable "database_password" {
  description = "Database password"
  type        = string
}

variable "lb_target_group_arn" {
  description = "ARN of the main load balancer target group"
  type        = string
}

variable "lb_security_group_id" {
  description = "id of the load balancer security group"
  type        = string
}

variable "db_security_group_id" {
  description = "id of the database security group"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of subnet ids to deploy the task to"
  type        = list(string)
}

variable "vpc_id" {
  description = "id of the VPC"
  type        = string
}

variable "app_url" {
  description = "Application public facing url"
  type        = string
}

variable "max_transcription_processes" {
  description = "maximum number of transcription processes to run"
  type        = number
}

variable "max_llm_processes" {
  description = "maximum number of llm processes to run"
  type        = number
}

variable "frontend_image_name" {
 description = "name of the frontend docker image to deploy"
  type        = string
}

variable "backend_image_name" {
  description = "name of the backend docker image to deploy"
  type        = string
}

variable "worker_image_name" {
  description = "name of the worker docker image to deploy"
  type        = string
}

variable "transcription_queue_name" {
  description = "name of transcription sqs queue"
  type = string
}

variable "transcription_deadletter_queue_name" {
  description = "name of transcription deadletter sqs queue"
  type = string
}

variable "llm_queue_name" {
  description = "name of llm sqs queue"
  type = string
}

variable "llm_deadletter_queue_name" {
  description = "name of llm deadletter sqs queue"
  type = string
}

variable "frontend_task_cpu" {
  description = "CPU units for the frontend ECS task definition"
  type        = number
  default     = 2048
}

variable "backend_task_cpu" {
  description = "CPU units for the backend ECS task definition"
  type        = number
  default     = 2048
}

variable "worker_task_cpu" {
  description = "CPU units for the backend ECS task definition"
  type        = number
  default     = 4096
}

variable "frontend_task_memory" {
  description = "Memory for the frontend ECS task definition"
  type        = number
  default     = 4096
}

variable "backend_task_memory" {
  description = "Memory for the backend ECS task definition"
  type        = number
  default     = 4096
}

variable "worker_task_memory" {
  description = "Memory for the backend ECS task definition"
  type        = number
  default     = 8192
}

variable "alb_arn" {
  description = "ARN of the Application Load Balancer, used for JWT signer validation"
  type        = string
}

variable "oidc_issuer" {
  description = "OIDC issuer URL, used for JWT issuer validation"
  type        = string
}

variable "aws_region" {
  description = "AWS region, used to construct the ALB public key endpoint URL"
  type        = string
}

variable "lb_listener_exists" {
  description = "Indicates whether the load balancer listener has been created"
  type        = bool
  default     = false
}

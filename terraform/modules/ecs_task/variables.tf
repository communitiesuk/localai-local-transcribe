variable "environment_name" {
  description = "must be one of: integration, test, nft, or production"
  type        = string
  validation {
    condition     = contains(["integration", "test", "nft", "production"], var.environment_name)
    error_message = "Environment must be one of: integration, test"
  }
}

variable "task_name" {
  description = "name of the task"
  type        = string
}

variable "container_port" {
  description = "the port the container will expose e.g. 8080"
  type        = number
}

variable "task_cpu" {
  type        = number
  description = "The amount of cpu units used by the ecs app task"
}

variable "task_memory" {
  type        = number
  description = "The amount of memory used by the ecs app task"
}


variable "container_image" {
  description = "the docker image the container should run"
  type        = string
}

variable "environment_variables" {
  description = "environment variables to pass to the container"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "secrets" {
  description = "secrets to pass to the container"
  type = list(object({
    name      = string
    valueFrom = string
  }))
  default = []
}

variable "ecs_task_execution_role_arn" {
  type        = string
  description = "The arn of the app task execution role"
}

variable "ecs_task_role_arn" {
  type        = string
  description = "The arn of the app task role"
}

variable "tags" {
  description = "A map of tags to assign to the resource."
  type        = map(string)
  default     = {}
}
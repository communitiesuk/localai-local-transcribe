variable "environment_name" {
  type        = string
  description = "Name of the environment, used to name resources, for example development"
}

variable "vpc_id" {
  type        = string
  description = "Id of the existing VPC that the evals subnet is created in"
}

variable "vpc_cidr_block" {
  type        = string
  description = "Address range of the existing VPC. The evals subnet is carved out of it"
}

variable "availability_zone" {
  type        = string
  description = "Availability zone the evals subnet is placed in. Evals tasks run once and stop, so one zone is enough"
}

variable "private_route_table_id" {
  type        = string
  description = "Id of the existing route table that sends internet traffic from private subnets to the NAT gateway"
}

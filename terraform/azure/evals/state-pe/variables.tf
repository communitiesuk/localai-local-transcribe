# Input variables for the state-account private endpoint bootstrap.

variable "subscription_id" {
  type        = string
  description = "Azure subscription that owns the state account and the evaluations virtual network."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group that holds the state account and will hold the private endpoint."
}

variable "location" {
  type        = string
  description = "Azure region for the private endpoint, for example uksouth."
  default     = "uksouth"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "storage_account_name" {
  type        = string
  description = "Name of the existing Terraform state storage account."
}

variable "storage_account_id" {
  type        = string
  description = "Resource ID of the existing Terraform state storage account. Passed in so this root does not read the account through the blob data plane."
}

variable "subnet_id" {
  type        = string
  description = "Resource ID of the private-endpoint subnet in the evaluations virtual network."
}

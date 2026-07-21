# Input variables for the evals blob storage stack.

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID that will own the evals storage account."
}

variable "resource_group_name" {
  type        = string
  description = "Existing resource group that will hold the evals storage account. Must already exist."
}

variable "location" {
  type        = string
  description = "Azure region for the evals storage account, for example uksouth."
}

variable "storage_account_name" {
  type        = string
  description = "Globally unique storage account name for evals data. 3 to 24 lowercase letters and digits only. Must differ from the Terraform state storage account name."
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example sandbox or assured."
}

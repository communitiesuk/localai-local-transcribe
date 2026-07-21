# Input variables for the Terraform state bootstrap stack.

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID that will own the Terraform state storage account."
}

variable "resource_group_name" {
  type        = string
  description = "Existing resource group that will hold the Terraform state storage account. Must already exist."
}

variable "location" {
  type        = string
  description = "Azure region for the state storage account, for example uksouth."
}

variable "storage_account_name" {
  type        = string
  description = "Globally unique storage account name for Terraform state. 3 to 24 lowercase letters and digits only."
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example sandbox or assured."
}

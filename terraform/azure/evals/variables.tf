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
  description = "Short environment label used in tags, for example Softwire sandbox or assured."
}

variable "account_replication_type" {
  type        = string
  description = "Storage replication type. Use LRS for Softwire sandbox. Set GRS or GZRS later if assured-env policy requires geo-redundancy."
  default     = "LRS"
}

variable "soft_delete_retention_days" {
  type        = number
  description = "Days to retain soft-deleted blobs and containers before permanent deletion."
  default     = 14
}

variable "sas_expiration_period" {
  type        = string
  description = "Maximum lifetime for newly created shared access signatures, as DD.HH:MM:SS."
  default     = "07.00:00:00"
}

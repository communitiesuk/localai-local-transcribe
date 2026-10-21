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
  default     = "uksouth"
}

variable "terraform_state_storage_account_name" {
  type        = string
  description = "Globally unique storage account name for Terraform state. 3 to 24 lowercase letters and digits only."
  default     = "ltevaltf"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "account_replication_type" {
  type        = string
  description = "Storage replication type. The test account uses LRS."
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

variable "shared_log_analytics_workspace_id" {
  type        = string
  description = "Resource ID of the shared Log Analytics workspace that Cyber can read. It is in another subscription, and its ID differs between test and production. The applying identity needs read and Microsoft.OperationalInsights/workspaces/sharedKeys/action on it, which the Monitoring Contributor role includes."
}

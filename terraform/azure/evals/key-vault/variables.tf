# Input variables for the evaluations storage Key Vault bootstrap.

variable "subscription_id" {
  type        = string
  description = "Azure subscription that will own the Key Vault."
}

variable "resource_group_name" {
  type        = string
  description = "Existing resource group that will hold the Key Vault. Must already exist."
}

variable "location" {
  type        = string
  description = "Azure region for the Key Vault, for example uksouth."
  default     = "uksouth"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "key_vault_name" {
  type        = string
  description = "Globally unique Key Vault name, 3 to 24 letters, digits, or hyphens."
  default     = "kv-tst-aielt-evals-001"
}

variable "storage_customer_managed_key_name" {
  type        = string
  description = "Name of the RSA key Storage will use to wrap the account encryption key."
  default     = "evals-storage"
}

variable "create_storage_key" {
  type        = bool
  description = "False on the first apply (vault only). True after Key Vault Crypto Officer has been granted, to create the key."
  default     = false
}

variable "soft_delete_retention_days" {
  type        = number
  description = "Days to retain a soft-deleted vault and its keys before they can be purged."
  default     = 90
}

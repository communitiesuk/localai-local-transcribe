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

variable "mhclg_ip_rules" {
  type        = list(string)
  description = "Public egress IPs or CIDR ranges for MHCLG devices allowed to reach the Terraform state backend."

  validation {
    condition     = length(var.mhclg_ip_rules) > 0 && !contains(var.mhclg_ip_rules, "0.0.0.0/0")
    error_message = "Set mhclg_ip_rules to at least one specific MHCLG public IP or CIDR range; do not use 0.0.0.0/0."
  }
}

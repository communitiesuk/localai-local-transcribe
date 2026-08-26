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

variable "terraform_state_storage_account_name" {
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

# The variables below are used only by the parent evals stack. They are declared here so
# the same terraform.tfvars file can be passed to this backend root module without warnings.

variable "sensitive_storage_account_name" {
  type        = string
  description = "Parent stack storage account name; ignored by the backend root module."
  default     = null
}

variable "results_storage_account_name" {
  type        = string
  description = "Parent stack storage account name; ignored by the backend root module."
  default     = null
}

variable "pipeline_identity_name" {
  type        = string
  description = "Parent stack pipeline identity name; ignored by the backend root module."
  default     = null
}

variable "ado_federation_issuer" {
  type        = string
  description = "Parent stack Azure DevOps federation issuer; ignored by the backend root module."
  default     = null
}

variable "ado_federation_subject" {
  type        = string
  description = "Parent stack Azure DevOps federation subject; ignored by the backend root module."
  default     = null
}

variable "adapt_ip_rules" {
  type        = list(string)
  description = "Parent stack ADAPT egress allowlist; ignored by the backend root module."
  default     = []
}

variable "ado_ip_rules" {
  type        = list(string)
  description = "Parent stack Azure DevOps egress allowlist; ignored by the backend root module."
  default     = []
}

variable "network_rules_bypass" {
  type        = list(string)
  description = "Parent stack storage firewall bypass setting; ignored by the backend root module."
  default     = []
}

variable "sensitive_public_network_access_enabled" {
  type        = bool
  description = "Parent stack sensitive account public endpoint flag; ignored by the backend root module."
  default     = null
}

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Parent stack private endpoint subnet ID; ignored by the backend root module."
  default     = null
}

variable "private_endpoint_vnet_id" {
  type        = string
  description = "Parent stack private endpoint VNet ID; ignored by the backend root module."
  default     = null
}

variable "private_endpoint_is_manual_connection" {
  type        = bool
  description = "Parent stack private endpoint manual connection flag; ignored by the backend root module."
  default     = null
}

variable "private_dns_zone_ids" {
  type        = list(string)
  description = "Parent stack private DNS zone IDs; ignored by the backend root module."
  default     = []
}

variable "input_writer_principal_ids" {
  type        = set(string)
  description = "Parent stack input writer principal IDs; ignored by the backend root module."
  default     = []
}

variable "debug_reader_principal_ids" {
  type        = set(string)
  description = "Parent stack debug reader principal IDs; ignored by the backend root module."
  default     = []
}

variable "results_reader_principal_ids" {
  type        = set(string)
  description = "Parent stack results reader principal IDs; ignored by the backend root module."
  default     = []
}

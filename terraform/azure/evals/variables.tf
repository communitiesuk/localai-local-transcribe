# Input variables for the evals blob storage stack.

variable "subscription_id" {
  type        = string
  description = "Azure subscription ID that will own the evals storage accounts."
}

variable "resource_group_name" {
  type        = string
  description = "Existing resource group that will hold the evals storage accounts. Must already exist."
}

variable "location" {
  type        = string
  description = "Azure region for the evals storage accounts, for example uksouth."
  default     = "uksouth"
}

variable "sensitive_storage_account_name" {
  type        = string
  description = "Globally unique name for the account holding the input and debug containers. Reachable from ADAPT only. 3 to 24 lowercase letters and digits."
  default     = "ltevalsen"
}

variable "results_storage_account_name" {
  type        = string
  description = "Globally unique name for the account holding the output (results) container. Reachable from ADAPT and MHCLG devices. 3 to 24 lowercase letters and digits."
  default     = "ltevalres"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "account_replication_type" {
  type        = string
  description = "Storage replication type. The test accounts use LRS."
  default     = "LRS"
}

variable "key_vault_name" {
  type        = string
  description = "Name of the Key Vault that holds the storage customer-managed key. Created by terraform/azure/evals/key-vault/."
  default     = "kv-tst-aielt-evals-001"
}

variable "storage_customer_managed_key_name" {
  type        = string
  description = "Name of the RSA key in that vault. Must already exist before this root is planned."
  default     = "evals-storage"
}

variable "storage_customer_managed_key_identity_name" {
  type        = string
  description = "User-assigned identity Storage uses to wrap and unwrap the customer-managed key. Not the evals job identity."
  default     = "evals-storage-key-id"
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

variable "pipeline_identity_name" {
  type        = string
  description = "Name of the user-assigned managed identity the Azure DevOps summarisation pipeline federates to."
  default     = "evals-blob-id"
}

variable "ado_federation_issuer" {
  type        = string
  description = "Issuer URL from the Azure DevOps workload-identity service connection. Set on the second apply to create the federated credential; leave null on the first apply."
  default     = null
}

variable "ado_federation_subject" {
  type        = string
  description = "Subject identifier from the Azure DevOps workload-identity service connection. Set alongside ado_federation_issuer."
  default     = null
}

# Network access

variable "network_rules_bypass" {
  type        = list(string)
  description = "Storage firewall bypass exemptions. Keep empty unless a named trusted Azure service needs access."
  default     = []
}

# Private endpoint

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Resource ID of the private endpoint subnet in the evals virtual network (created by the vnet/ root). Both blob private endpoints are placed in it."
}

# Team RBAC
#
# All values are Entra ID object IDs. Prefer a group object ID over individual users so
# membership changes do not need a terraform apply.

variable "input_writer_principal_ids" {
  type        = set(string)
  description = "Object IDs allowed to upload and manage eval test data in the input container. Keep to the people who curate that data."
  default     = []
}

variable "debug_reader_principal_ids" {
  type        = set(string)
  description = "Object IDs allowed to read the debug container when diagnosing eval runs."
  default     = []
}

variable "results_reader_principal_ids" {
  type        = set(string)
  description = "Object IDs allowed to read the output (results) container."
  default     = []
}

variable "debug_and_output_writer_principal_ids" {
  type        = set(string)
  description = "Object IDs allowed to read, write and delete blobs in both the debug container and the output container. An ad hoc evals run on test ADAPT writes both, so one list grants both roles."
  default     = []
}

# Shared logging

variable "terraform_state_storage_account_name" {
  type        = string
  description = "Name of the Terraform state storage account created by backend/. This root does not manage that account. It only needs the name to attach the shared diagnostic settings to it."
}

variable "shared_log_analytics_workspace_id" {
  type        = string
  description = "Resource ID of the shared Log Analytics workspace that receives every evals diagnostic log. Cyber and the team both read it. It is in another subscription, and its ID differs between test and production. The applying identity needs read and Microsoft.OperationalInsights/workspaces/sharedKeys/action on it, which the Monitoring Contributor role includes."
}

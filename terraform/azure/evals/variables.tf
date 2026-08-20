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
}

variable "sensitive_storage_account_name" {
  type        = string
  description = "Globally unique name for the account holding the input and debug containers. Reachable from ADAPT only. 3 to 24 lowercase letters and digits."
}

variable "results_storage_account_name" {
  type        = string
  description = "Globally unique name for the account holding the output (results) container. Reachable from ADAPT and MHCLG devices. 3 to 24 lowercase letters and digits."
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example sandbox or assured."
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
#
# Public IPv4 addresses or CIDR ranges. Use plain IPs for single-host entries.

variable "adapt_ip_rules" {
  type        = list(string)
  description = "Public egress IPs or CIDR ranges for ADAPT. Allowed on both accounts."
  default     = []
}

variable "ado_ip_rules" {
  type        = list(string)
  description = "Temporary public egress IPs or CIDR ranges for Azure DevOps agents. Allowed on both accounts."
  default     = []
}

variable "mhclg_ip_rules" {
  type        = list(string)
  description = "Public egress IPs or CIDR ranges for MHCLG devices. Allowed on the results account only."
  default     = []
}

variable "network_rules_bypass" {
  type        = list(string)
  description = "Storage firewall bypass exemptions. Keep empty unless a named trusted Azure service needs access."
  default     = []
}

variable "sensitive_public_network_access_enabled" {
  type        = bool
  description = "Whether the input/debug account keeps a public endpoint. Set false once ADAPT confirms the private endpoint works, which makes the private endpoint the only route in and ignores adapt_ip_rules."
  default     = true
}

# Private endpoint
#
# Leave private_endpoint_subnet_id null when the ADAPT team creates the endpoint from their
# own subscription. See network.tf.

variable "private_endpoint_subnet_id" {
  type        = string
  description = "Resource ID of the ADAPT subnet to place the blob private endpoints in. Null means this stack creates no endpoint."
  default     = null
}

variable "private_endpoint_is_manual_connection" {
  type        = bool
  description = "True when the subnet and the storage accounts have different owners, leaving the connection pending ADAPT approval."
  default     = false
}

variable "private_dns_zone_ids" {
  type        = list(string)
  description = "Resource IDs of existing privatelink.blob.core.windows.net private DNS zones to register the endpoints in. If empty and this stack creates private endpoints, it also creates and links a private DNS zone."
  default     = []
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

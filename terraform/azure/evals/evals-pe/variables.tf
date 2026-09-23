# Input variables for the evaluations-account blob private endpoints.

variable "subscription_id" {
  type        = string
  description = "Azure subscription that owns the evaluations accounts and the evaluations virtual network."
}

variable "resource_group_name" {
  type        = string
  description = "Resource group that holds the evaluations accounts and will hold the private endpoints."
}

variable "location" {
  type        = string
  description = "Azure region for the private endpoints, for example uksouth."
  default     = "uksouth"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "subnet_id" {
  type        = string
  description = "Resource ID of the private-endpoint subnet in the evaluations virtual network."
}

variable "storage_accounts" {
  type = map(object({
    name    = string
    id      = string
    purpose = string
  }))
  description = "Evaluations storage accounts to attach a blob private endpoint to. IDs are passed in so this root does not read the accounts through the blob data plane."
}

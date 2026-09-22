# Input variables for the evaluations virtual network bootstrap.

variable "subscription_id" {
  type        = string
  description = "Azure subscription that will own the virtual network."
}

variable "resource_group_name" {
  type        = string
  description = "Existing resource group that will hold the virtual network. Must already exist."
}

variable "location" {
  type        = string
  description = "Azure region for the virtual network, for example uksouth."
  default     = "uksouth"
}

variable "environment_name" {
  type        = string
  description = "Short environment label used in tags, for example test."
}

variable "virtual_network_name" {
  type        = string
  description = "Name of the evaluations virtual network."
  default     = "vnet-tst-uks-aielt-evals-001"
}

variable "subnet_name" {
  type        = string
  description = "Name of the subnet used only for blob private endpoints."
  default     = "snet-tst-uks-aielt-pe-001"
}

variable "address_space" {
  type        = list(string)
  description = "Address prefixes for the virtual network, for example [\"10.x.x.0/24\"]. Must not overlap the hub."
}

variable "subnet_prefix" {
  type        = string
  description = "Address prefix for the private-endpoint subnet. Must sit inside address_space."
}

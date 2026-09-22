# Evaluations virtual network and the subnet that will hold blob private endpoints.
# Apply once from the test desktop with local state. Do not apply this root on vmss-shared:
# that pool cannot reach the remote state account yet, and agent-local state is ephemeral.
#
# Peering to the hub and the private endpoints themselves are not in this root. Message Nas
# with the virtual network resource ID after apply; peering is a pair of objects and he
# creates the hub side. Endpoints come after the peer exists so the spoke can use hub DNS.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_virtual_network" "evals" {
  name                = var.virtual_network_name
  location            = var.location
  resource_group_name = var.resource_group_name
  address_space       = var.address_space

  tags = {
    purpose     = "evals-private-endpoints"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_subnet" "private_endpoints" {
  name                 = var.subnet_name
  resource_group_name  = var.resource_group_name
  virtual_network_name = azurerm_virtual_network.evals.name
  address_prefixes     = [var.subnet_prefix]

  # Private endpoints cannot be created in a subnet that still enforces network policies.
  private_endpoint_network_policies = "Disabled"
}

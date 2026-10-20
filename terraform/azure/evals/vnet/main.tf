# Evaluations virtual network and the subnet that holds the private endpoints.
# The network security group for that subnet is in nsg.tf.
# Apply from test ADAPT with the local state for this root. Do not apply this root
# from a shared Azure DevOps agent. That apply would not see this state and would
# try to create the network again.
#
# Peering to the hub and the private endpoints themselves are not in this root.
# Peering is a pair of objects and the Azure team creates the hub side.
# Endpoints come after the peer exists so the spoke can use hub DNS.

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

  # Enabled so the network security group on this subnet applies to private endpoint traffic.
  # Azure ignores that group for traffic to the endpoints when this setting is Disabled.
  # The same setting also honours a route table on private endpoint traffic. This subnet has no route table.
  # Existing private endpoints stay in the subnet.
  private_endpoint_network_policies = "Enabled"
}

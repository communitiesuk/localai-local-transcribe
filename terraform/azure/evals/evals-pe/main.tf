# Blob private endpoints for the two evaluations storage accounts.
# Apply from the test desktop with local state. Do not set private_endpoint_subnet_id
# on the parent evals root: that root also writes a Domain Name System zone group,
# and this subscription cannot write the hub zone.
#
# Domain Name System is not in this root. This subscription cannot write the hub
# privatelink.blob.core.windows.net zone. The Azure team attaches each endpoint to that
# zone after it exists, the same as pe-aieltevalstftst001-blob.

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

resource "azurerm_private_endpoint" "evals_blob" {
  for_each = var.storage_accounts

  name                = "pe-${each.value.name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${each.value.name}-blob"
    private_connection_resource_id = each.value.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  tags = {
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }

  # The Azure team adds the hub DNS zone group outside Terraform. Without this, a re-apply
  # would remove it and the account names would stop resolving to the private addresses.
  lifecycle {
    ignore_changes = [private_dns_zone_group]
  }
}

# First blob private endpoint on the Terraform state account.
# Apply from the test desktop with local state. Do not apply the parent evals root for this:
# that root stores remote state on this account and cannot init until the endpoint exists.
#
# Do not create a privatelink.blob.core.windows.net zone here. Pass the hub zone resource ID
# so the endpoint joins the existing zone. A new zone in the team resource group will not
# be seen by agents that use hub Domain Name System.

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

resource "azurerm_private_endpoint" "state_blob" {
  name                = "pe-${var.storage_account_name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "psc-${var.storage_account_name}-blob"
    private_connection_resource_id = var.storage_account_id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name                 = "blob-privatelink"
    private_dns_zone_ids = [var.private_dns_zone_id]
  }

  tags = {
    purpose     = "evals-terraform-state"
    workload    = "evals"
    environment = var.environment_name
  }
}

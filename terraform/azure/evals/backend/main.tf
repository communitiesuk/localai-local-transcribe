# Bootstrap remote Terraform state storage for the evals Azure stack.
# Apply this once with a local backend before the parent stack can use azurerm remote state.
#
# SANDBOX vs ASSURED ENVIRONMENT:
# - Transferable: resource shape (storage account + tfstate container + blob versioning).
# - Must adapt: resource_group_name, location, storage_account_name, subscription.
# - Uncertain until assured env exists: whether a dedicated resource group is provided,
#   naming conventions, and whether state must live in a central platform subscription.

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

resource "azurerm_storage_account" "terraform_state" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  # Soft-delete and versioning protect state from accidental overwrite or delete.
  blob_properties {
    versioning_enabled = true
  }

  tags = {
    purpose     = "terraform-state"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_storage_container" "terraform_state" {
  name                  = "tfstate"
  storage_account_id    = azurerm_storage_account.terraform_state.id
  container_access_type = "private"
}

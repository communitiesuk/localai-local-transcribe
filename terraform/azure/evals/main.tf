# Evals Azure Blob Storage: storage account plus input, debug, and output containers.
#
# SANDBOX vs ASSURED ENVIRONMENT:
# - Transferable: three private containers named input, debug, and output; storage account
#   shape; remote state via azurerm backend; manual plan/apply from Cloud Shell.
# - Must adapt: subscription_id, resource_group_name, location, storage_account_name,
#   environment_name, and the backend block values after the assured environment exists.
# - Uncertain: final naming conventions, whether containers need Azure metadata beyond
#   names, and whether the storage account must sit in a platform-owned resource group.
# - Out of scope for the original ticket: private endpoints, RBAC, network restrictions,
#   and populating containers with data. Soft delete and SAS expiry are included here as
#   low-regret hardening ahead of the assured environment.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }

  # Partial backend: pass resource_group_name, storage_account_name, container_name, and key
  # at init time via -backend-config after the backend stack has been applied.
  backend "azurerm" {}
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

resource "azurerm_storage_account" "evals" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  # Harden defaults that do not require network lockdown, RBAC, or private endpoints.
  allow_nested_items_to_be_public = false
  local_user_enabled              = false
  default_to_oauth_authentication = true

  # Cap how long a newly created SAS token may remain valid.
  sas_policy {
    expiration_period = var.sas_expiration_period
    expiration_action = "Log"
  }

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = var.soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.soft_delete_retention_days
    }
  }

  tags = {
    purpose     = "evals-pipeline-data"
    workload    = "evals"
    environment = var.environment_name
  }
}

# Azure does not support resource tags on blob containers. Container identity is the
# name; purpose is also recorded as blob metadata for inspection in the portal.
resource "azurerm_storage_container" "input" {
  name                  = "input"
  storage_account_id    = azurerm_storage_account.evals.id
  container_access_type = "private"

  metadata = {
    purpose = "input"
  }
}

resource "azurerm_storage_container" "debug" {
  name                  = "debug"
  storage_account_id    = azurerm_storage_account.evals.id
  container_access_type = "private"

  metadata = {
    purpose = "debug"
  }
}

resource "azurerm_storage_container" "output" {
  name                  = "output"
  storage_account_id    = azurerm_storage_account.evals.id
  container_access_type = "private"

  metadata = {
    purpose = "output"
  }
}

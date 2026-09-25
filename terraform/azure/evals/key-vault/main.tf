# Key Vault that holds the customer-managed key for the two evaluations storage accounts.
# Apply from the test desktop with local state. Creating the key is Key Vault data plane:
# vmss-shared has no public egress, so do not create the key on that pool until a vault
# private endpoint and hub Domain Name System exist.
#
# First apply: vault only (create_storage_key = false). Privileged Identity Management
# Contributor can create the vault. It cannot grant Key Vault Crypto Officer, and without
# that role it cannot create the key. The pipeline grant-key-vault-roles command does
# those assignments. Second apply: set create_storage_key = true and apply the key.
#
# Purge protection cannot be turned off once set. Public access stays on until a private
# endpoint is proven. Trusted Microsoft services may bypass the firewall so Storage can
# wrap and unwrap before Domain Name System is attached.

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
  features {
    key_vault {
      # Destroying the Terraform resource must not purge the vault. Purge protection
      # is required for Storage customer-managed keys and cannot be disabled later.
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id
}

data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "evals_storage" {
  name                = var.key_vault_name
  location            = var.location
  resource_group_name = var.resource_group_name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"

  rbac_authorization_enabled    = true
  purge_protection_enabled      = true
  soft_delete_retention_days    = var.soft_delete_retention_days
  public_network_access_enabled = true

  # Allow until the vault private endpoint is proven. AzureServices lets Storage wrap
  # and unwrap the account encryption key without a private name lookup.
  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = {
    purpose     = "evals-storage-customer-managed-key"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_key_vault_key" "evals_storage" {
  count = var.create_storage_key ? 1 : 0

  name         = var.storage_customer_managed_key_name
  key_vault_id = azurerm_key_vault.evals_storage.id
  key_type     = "RSA"
  key_size     = 2048

  # Storage wrap and unwrap only. Do not pin a version in the parent storage accounts
  # so a later Key Vault rotation is picked up.
  key_opts = [
    "unwrapKey",
    "wrapKey",
  ]

  tags = {
    purpose     = "evals-storage-customer-managed-key"
    workload    = "evals"
    environment = var.environment_name
  }
}

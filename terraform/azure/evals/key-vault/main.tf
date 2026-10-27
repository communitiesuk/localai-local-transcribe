# Key Vault that holds the customer-managed key for the two evaluations storage accounts.
# Apply from test ADAPT with local state. An apply from a shared agent would not see that state.
#
# First apply: vault only (create_storage_key = false). Privileged Identity Management
# Contributor can create the vault. It cannot grant Key Vault Crypto Officer, and without
# that role it cannot create the key. The pipeline grant-key-vault-roles command does
# those assignments. Second apply: set create_storage_key = true and apply the key.
#
# Purge protection cannot be turned off once set. Public data-plane access is off.
# The private endpoint is the path in, proven from test ADAPT on 20 October 2026.
# The AzureServices exception stays, so Azure Storage can still encrypt the
# accounts with this customer-managed key.
#
# The key rotates itself once a year through its rotation policy. Vault audit logs
# go to the evals Log Analytics workspace. Test ADAPT reaches the vault through the
# Zscaler mapping of its private name.

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
  public_network_access_enabled = false

  # Private endpoint proven from test ADAPT on 20 October 2026.
  # AzureServices stays so Azure Storage can still encrypt the accounts with this key.
  network_acls {
    default_action = "Deny"
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

  # A new key version is created one year after the current one, matching the yearly
  # rotation used for the AWS KMS keys elsewhere in this repository. Each version expires
  # after 15 months. The three months between rotation and expiry leave time to notice
  # and fix a failed rotation, because an expired key stops Storage reaching the data.
  # Key Vault requires expiry to be at least 28 days later than rotation.
  #
  # The provider requires notify_before_expiry with expire_after. It publishes a "near
  # expiry" event 30 days before expiry. Nothing subscribes to that event yet.
  rotation_policy {
    expire_after         = "P15M"
    notify_before_expiry = "P30D"

    automatic {
      time_after_creation = "P1Y"
    }
  }

  # Each rotation gives the current version a new expiry date, which would otherwise show
  # as drift. Changing expiration_date to an earlier date also forces the key to be
  # replaced, which would cut Storage off from the data. The current version gets its
  # expiry from the policy by rotating once by hand after the first apply.
  lifecycle {
    ignore_changes = [expiration_date]
  }

  tags = {
    purpose     = "evals-storage-customer-managed-key"
    workload    = "evals"
    environment = var.environment_name
  }
}

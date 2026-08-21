# Evals Azure Blob Storage: two storage accounts split by who is allowed to reach them.
#
# Why two accounts: Azure storage firewall rules (network ACLs and private endpoints) are
# scoped to the storage account, not the container. The access requirement differs per
# container - input and debug must be reachable only from ADAPT, results must also be
# readable from MHCLG devices.
#
#   sensitive account -> input, debug   (ADAPT IPs; private endpoint approach TBD)
#   results account   -> output         (ADAPT IPs, MHCLG IPs; private endpoint approach TBD)
#
# Softwire sandbox vs assured Azure environment:
# - Transferable: the two-account split, container names, hardening defaults, private
#   endpoint and RBAC shape, remote state via azurerm backend, manual plan/apply.
# - Must adapt: tenant, subscription_id, resource_group_name, location, both storage
#   account names, environment_name, all IP allowlists, the private endpoint subnet and
#   DNS zones, all principal IDs, and backend -backend-config values.
# - Uncertain: whether ADAPT owns the private endpoint (see network.tf), and whether the
#   platform mandates a naming prefix or a platform-owned resource group.

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

  # Both accounts disable shared access keys, so the provider must use Entra ID for any
  # data plane call it makes.
  storage_use_azuread = true
}

locals {
  adapt_ip_rules = distinct(var.adapt_ip_rules)
  # TODO(AIILG-649): Confirm the Azure DevOps network route once we can test this in the
  # Azure environment, then remove any allowlist entries that private networking makes
  # unnecessary.
  ado_ip_rules   = distinct(var.ado_ip_rules)
  mhclg_ip_rules = distinct(var.mhclg_ip_rules)

  # Per-account settings. Hardening common to both is set once on the resource below so the
  # two accounts cannot drift apart.
  accounts = {
    sensitive = {
      name    = var.sensitive_storage_account_name
      purpose = "evals-input-and-debug"
      # TODO(AIILG-649): Confirm whether these temporary Azure DevOps IP rules are still
      # needed once the private networking shape is known in the Azure environment.
      ip_rules = concat(local.adapt_ip_rules, local.ado_ip_rules)
      # TODO(AIILG-649): Confirm when this can be disabled once the private endpoint
      # configuration is known and tested in the Azure environment.
      public_network_access_enabled = var.sensitive_public_network_access_enabled
    }
    results = {
      name    = var.results_storage_account_name
      purpose = "evals-results"
      # TODO(AIILG-649): Confirm whether these temporary Azure DevOps IP rules are still
      # needed once the private networking shape is known in the Azure environment.
      ip_rules = concat(local.adapt_ip_rules, local.mhclg_ip_rules, local.ado_ip_rules)
      # Results intentionally keep public network access so approved MHCLG devices can read them.
      public_network_access_enabled = true
    }
  }

  # Container name -> the account key in local.accounts that holds it.
  containers = {
    input  = "sensitive"
    debug  = "sensitive"
    output = "results"
  }
}

resource "azurerm_storage_account" "evals" {
  for_each = local.accounts

  name                     = each.value.name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  allow_nested_items_to_be_public = false
  local_user_enabled              = false
  default_to_oauth_authentication = true

  # Shared access keys are the main way to bypass RBAC from the portal or a SAS token.
  # With them disabled every data plane call must present an Entra ID token, so the role
  # assignments in rbac.tf are the only route to the data.
  shared_access_key_enabled = false

  # TODO(AIILG-649): Keep this configurable until the Azure environment confirms what the
  # private endpoint setup looks like. When set false, the public IP allowlist no longer
  # provides access to the account.
  public_network_access_enabled = each.value.public_network_access_enabled

  # Deny by default. With both allowlists empty, public network access is denied while the
  # final private networking approach is still to be confirmed in the Azure environment.
  network_rules {
    default_action = "Deny"
    bypass         = var.network_rules_bypass
    ip_rules       = each.value.ip_rules
  }

  # Cap how long a newly created SAS token may remain valid. With shared keys disabled only
  # user delegation SAS is possible, and that is still bound by RBAC and the firewall.
  sas_policy {
    expiration_period = var.sas_expiration_period
    expiration_action = "Block"
  }

  # Versioning and soft delete protect blobs and containers from accidental overwrite or delete.
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
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }
}

# Azure does not support resource tags on blob containers. Container identity is the name;
# purpose is also recorded as blob metadata for inspection in the portal. These are managed
# through the resource manager API, so container creation is not blocked by the firewall.
resource "azurerm_storage_container" "evals" {
  for_each = local.containers

  name                  = each.key
  storage_account_id    = azurerm_storage_account.evals[each.value].id
  container_access_type = "private"

  metadata = {
    purpose = each.key
  }
}

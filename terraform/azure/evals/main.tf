# Evals Azure Blob Storage: two storage accounts split by who is allowed to reach them.
#
# Why two accounts: Azure storage firewall rules (network ACLs and private endpoints) are
# scoped to the storage account, not the container. The access requirement differs per
# container - input and debug must be reachable only from ADAPT, results must also be
# readable from MHCLG devices.
#
#   sensitive account holds input and debug. Reached only through its private endpoint.
#   results account holds output. Reached through its private endpoint, public access kept.

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
  features {
    key_vault {
      purge_soft_delete_on_destroy    = false
      recover_soft_deleted_key_vaults = true
    }
  }
  subscription_id = var.subscription_id

  # Both accounts disable shared access keys, so the provider must use Entra ID for any
  # data plane call it makes.
  storage_use_azuread = true
}

locals {
  # Per-account settings. Hardening common to both is set once on the resource below so the
  # two accounts cannot drift apart.
  accounts = {
    sensitive = {
      name    = var.sensitive_storage_account_name
      purpose = "evals-input-and-debug"
    }
    results = {
      name    = var.results_storage_account_name
      purpose = "evals-results"
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

  # Create-time only: changing this forces replacement and destroys data.
  infrastructure_encryption_enabled = true

  # Create-time only. Account lets the customer-managed key cover Table and Queue.
  # Service (the Azure default) cannot be changed later without replacing the account.
  table_encryption_key_type = "Account"
  queue_encryption_key_type = "Account"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.storage_customer_managed_key.id]
  }

  # Versionless key ID so a later Key Vault rotation is picked up without a Terraform change.
  customer_managed_key {
    key_vault_key_id          = data.azurerm_key_vault_key.evals_storage.versionless_id
    user_assigned_identity_id = azurerm_user_assigned_identity.storage_customer_managed_key.id
  }

  allow_nested_items_to_be_public = false
  local_user_enabled              = false
  default_to_oauth_authentication = true

  # Shared access keys are the main way to bypass RBAC from the portal or a SAS token.
  # With them disabled every data plane call must present an Entra ID token, so the role
  # assignments in rbac.tf are the only route to the data.
  shared_access_key_enabled = false

  # Both accounts are reached only through their private endpoints, so there is no public
  # endpoint and no IP allowlist. Read access from MHCLG devices to results is added over
  # private connectivity, not by reopening public access.
  public_network_access_enabled = false

  network_rules {
    default_action = "Deny"
    # AzureServices is the trusted Microsoft services exception. The live accounts
    # regain it after an apply that clears it, so Terraform keeps the value.
    # Confirmed by the engineering team.
    bypass = var.network_rules_bypass
    # Set explicitly because the provider keeps the live list when this is left out.
    ip_rules = []
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

  # The workload uses blobs rather than Azure Files. Azure still exposes the File service on a
  # standard account. Defaults still allow SMB 2.1 and 3.0, NTLMv2, and AES-128 channel
  # encryption. These settings are the File-protocol floor Wiz requires. They do not create
  # a file share. Kerberos ticket encryption is set to AES-256 so RC4 is not left as a default.
  share_properties {
    smb {
      versions                        = ["SMB3.1.1"]
      authentication_types            = ["Kerberos"]
      channel_encryption_type         = ["AES-256-GCM"]
      kerberos_ticket_encryption_type = ["AES-256"]
    }
  }

  tags = {
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }

  # Creates the Key Vault role before the account. It does not wait for the role to take effect,
  # which can take minutes, so a first apply can still fail to wrap the key. Rerun the apply if so.
  depends_on = [azurerm_role_assignment.storage_customer_managed_key]
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

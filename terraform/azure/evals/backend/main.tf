# Bootstrap remote Terraform state storage for the evals Azure stack.
# Apply this once with a local backend before the parent stack can use azurerm remote state.
#
# Softwire sandbox vs assured Azure environment:
# - Transferable: storage account plus tfstate container; versioning; soft delete; SAS expiry;
#   auth defaults; manual plan/apply from Cloud Shell.
# - Must adapt: tenant, subscription_id, resource_group_name, location,
#   terraform_state_storage_account_name, environment_name. Assured may be a different tenant;
#   use a new state storage account name.
# - Uncertain until assured env exists: whether a dedicated resource group is provided,
#   naming conventions, and whether state must live in a central platform subscription.
# - Local terraform.tfstate for this bootstrap is gitignored. If Cloud Shell home is wiped,
#   import the existing state storage account and tfstate container before applying again.

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

  # The state account disables shared access keys, so the provider must use Entra ID for
  # any storage data plane calls it makes.
  storage_use_azuread = true
}

resource "azurerm_storage_account" "terraform_state" {
  name                     = var.terraform_state_storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = var.account_replication_type

  # Create-time only: changing this forces replacement and destroys data.
  infrastructure_encryption_enabled = true

  public_network_access_enabled = true

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
    ip_rules       = distinct(var.mhclg_ip_rules)
  }

  # Harden defaults that do not require private endpoints.
  allow_nested_items_to_be_public = false
  local_user_enabled              = false
  default_to_oauth_authentication = true
  shared_access_key_enabled       = false

  # Cap how long a newly created SAS token may remain valid. Block over-long SAS on the state
  # account too — it holds Terraform state, which can contain sensitive values.
  sas_policy {
    expiration_period = var.sas_expiration_period
    expiration_action = "Block"
  }

  # Versioning and soft delete protect state from accidental overwrite or delete.
  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = var.soft_delete_retention_days
    }

    container_delete_retention_policy {
      days = var.soft_delete_retention_days
    }
  }

  # Remote state uses blobs rather than Azure Files. Azure still exposes the File service on a
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

# Bootstrap remote Terraform state storage for the evals Azure stack.
# Apply this once from test ADAPT with local state, before the parent stack can use remote state.
# The local terraform.tfstate is gitignored. A copy is kept on SharePoint.
# If the test ADAPT profile is wiped, restore that copy before applying again.

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

  # State is reached only through its private endpoint, so no public address is allowed.
  # The storage firewall does not gate the resource manager API, so this account can still
  # be changed, and public access turned back on, from the Portal.
  public_network_access_enabled = false

  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
    # Set explicitly because the provider keeps the live list when this is left out.
    ip_rules = []
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

# Private endpoint for the state account. It is kept in this root, with local state, and not in
# the parent root. The parent root keeps its remote state on this account and reads it through
# this endpoint on every plan and apply. If the pipeline replaced the endpoint mid-apply, it would
# lose its route to its own state.
#
# The endpoint was first created from test ADAPT on 22 September 2026 by a separate root,
# state-pe/. It is brought into this root with terraform import, so nothing is recreated.
#
# Domain Name System is not in this root. This identity cannot write the hub
# privatelink.blob.core.windows.net zone. The Azure team attaches the endpoint to that
# zone after it exists.
resource "azurerm_private_endpoint" "state_blob" {
  name                = "pe-${azurerm_storage_account.terraform_state.name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-${azurerm_storage_account.terraform_state.name}-blob"
    private_connection_resource_id = azurerm_storage_account.terraform_state.id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  tags = {
    purpose     = "evals-terraform-state"
    workload    = "evals"
    environment = var.environment_name
  }

  # The Azure team adds the hub DNS zone group outside Terraform. Without this, an apply
  # would remove it and the account name would stop resolving to the private address.
  lifecycle {
    ignore_changes = [private_dns_zone_group]
  }
}

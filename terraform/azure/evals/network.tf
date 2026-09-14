# TODO(AIILG-649): Private endpoints are blocked on the new Azure environment.
# For now this uses storage network IP restrictions, not proper private networking.
#
# Who creates the endpoint depends on where the ADAPT VNet lives:
# - Same subscription as this stack: set private_endpoint_subnet_id and this stack creates it.
# - ADAPT-owned subscription or tenant: leave private_endpoint_subnet_id null. The ADAPT team
#   creates the endpoint in their own VNet against the storage account IDs from outputs.tf,
#   and we approve the pending connection (see README).
#
# DNS: the endpoint only resolves privately once privatelink.blob.core.windows.net is linked
# to the ADAPT VNet. Pass existing zones via private_dns_zone_ids, or set
# private_endpoint_vnet_id so this stack creates and links a zone when it creates the endpoint.

locals {
  create_private_endpoint      = var.private_endpoint_subnet_id != null
  create_blob_private_dns_zone = local.create_private_endpoint && length(var.private_dns_zone_ids) == 0 && var.private_endpoint_vnet_id != null
  blob_private_dns_zone_ids    = length(var.private_dns_zone_ids) > 0 ? var.private_dns_zone_ids : azurerm_private_dns_zone.blob[*].id
}

resource "azurerm_private_dns_zone" "blob" {
  count = local.create_blob_private_dns_zone ? 1 : 0

  name                = "privatelink.blob.core.windows.net"
  resource_group_name = var.resource_group_name

  tags = {
    purpose     = "evals-blob-private-dns"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_private_dns_zone_virtual_network_link" "blob" {
  count = local.create_blob_private_dns_zone ? 1 : 0

  name                  = "pdz-link-${var.environment_name}-blob"
  resource_group_name   = var.resource_group_name
  private_dns_zone_name = azurerm_private_dns_zone.blob[0].name
  virtual_network_id    = var.private_endpoint_vnet_id
  registration_enabled  = false

  tags = {
    purpose     = "evals-blob-private-dns"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_private_endpoint" "blob" {
  for_each = { for key, account in local.accounts : key => account if local.create_private_endpoint }

  name                = "pe-${each.value.name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-${each.value.name}-blob"
    private_connection_resource_id = azurerm_storage_account.evals[each.key].id
    subresource_names              = ["blob"]

    # True when the subnet owner and the storage account owner are different parties, which
    # leaves the connection pending until ADAPT approves it.
    is_manual_connection = var.private_endpoint_is_manual_connection
    request_message      = var.private_endpoint_is_manual_connection ? "Local Transcribe evals blob access" : null
  }

  private_dns_zone_group {
    name                 = "blob-privatelink"
    private_dns_zone_ids = local.blob_private_dns_zone_ids
  }

  lifecycle {
    precondition {
      condition     = length(local.blob_private_dns_zone_ids) > 0
      error_message = "Set private_dns_zone_ids to existing zone IDs, or set private_endpoint_vnet_id so Terraform can create and link a private DNS zone."
    }
  }

  tags = {
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }
}

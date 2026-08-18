# Private endpoints so ADAPT reaches blob storage over a private connection rather than the
# public endpoint.
#
# Who creates the endpoint depends on where the ADAPT VNet lives:
# - Same subscription as this stack: set private_endpoint_subnet_id and this stack creates it.
# - ADAPT-owned subscription or tenant: leave private_endpoint_subnet_id null. The ADAPT team
#   creates the endpoint in their own VNet against the storage account IDs from outputs.tf,
#   and we approve the pending connection (see README).
#
# DNS: the endpoint only resolves privately once privatelink.blob.core.windows.net is linked
# to the ADAPT VNet. Pass the zone via private_dns_zone_ids if we own it; if the platform
# manages DNS centrally, leave it empty and ask ADAPT to add the A records.

resource "azurerm_private_endpoint" "blob" {
  for_each = { for key, account in local.accounts : key => account if var.private_endpoint_subnet_id != null }

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

  dynamic "private_dns_zone_group" {
    for_each = length(var.private_dns_zone_ids) == 0 ? [] : [1]

    content {
      name                 = "blob-privatelink"
      private_dns_zone_ids = var.private_dns_zone_ids
    }
  }

  tags = {
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }
}

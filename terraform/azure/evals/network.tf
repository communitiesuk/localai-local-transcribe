# Blob private endpoints for the two evals storage accounts, in the evals virtual network.
#
# Domain Name System is not in this root. This subscription cannot write the hub
# privatelink.blob.core.windows.net zone. The Azure team attaches each endpoint to that
# zone after it exists, the same as the state account endpoint in state-pe/.

resource "azurerm_private_endpoint" "blob" {
  for_each = local.accounts

  name                = "pe-${each.value.name}-blob"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-${each.value.name}-blob"
    private_connection_resource_id = azurerm_storage_account.evals[each.key].id
    subresource_names              = ["blob"]
    is_manual_connection           = false
  }

  tags = {
    purpose     = each.value.purpose
    workload    = "evals"
    environment = var.environment_name
  }

  # The Azure team adds the hub DNS zone group outside Terraform. Without this, an apply
  # would remove it and the account names would stop resolving to the private addresses.
  lifecycle {
    ignore_changes = [private_dns_zone_group]
  }
}

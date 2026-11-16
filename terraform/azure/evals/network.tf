# Private endpoints in the evals virtual network. One blob endpoint per evals storage account,
# and one endpoint for the vault that holds the storage customer-managed key.
#
# Domain Name System is not in this root. This subscription cannot write the hub
# privatelink.blob.core.windows.net or privatelink.vaultcore.azure.net zones. The Azure team
# attaches each endpoint to its hub zone after it exists, the same as the state account
# endpoint in backend/.

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

# The vault itself is created by key-vault/ on the test desktop. The endpoint lives here so the
# pipeline manages it with remote state.
resource "azurerm_private_endpoint" "key_vault" {
  name                = "pe-${data.azurerm_key_vault.evals_storage.name}-vault"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-${data.azurerm_key_vault.evals_storage.name}-vault"
    private_connection_resource_id = data.azurerm_key_vault.evals_storage.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  tags = {
    purpose     = "evals-storage-customer-managed-key"
    workload    = "evals"
    environment = var.environment_name
  }

  # The Azure team adds the hub DNS zone group outside Terraform. Without this, an apply
  # would remove it and the vault name would stop resolving to the private address.
  lifecycle {
    ignore_changes = [private_dns_zone_group]
  }
}

# Customer-managed key for both evaluations storage accounts.
#
# The vault and the RSA key are created by terraform/azure/evals/key-vault/ on the
# test desktop. This file reads them, creates a dedicated user-assigned identity
# (not evals-blob-id, which is the job principal), grants that identity wrap and
# unwrap, and the storage accounts in main.tf attach the key.
#
# Parent plan will fail until the key exists. Do not apply the current accounts
# without this file: Table and Queue Account is create-time only.

data "azurerm_key_vault" "evals_storage" {
  name                = var.key_vault_name
  resource_group_name = var.resource_group_name
}

data "azurerm_key_vault_key" "evals_storage" {
  name         = var.storage_customer_managed_key_name
  key_vault_id = data.azurerm_key_vault.evals_storage.id
}

resource "azurerm_user_assigned_identity" "storage_customer_managed_key" {
  name                = var.storage_customer_managed_key_identity_name
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = {
    purpose     = "evals-storage-customer-managed-key"
    workload    = "evals"
    environment = var.environment_name
  }
}

# Storage calls wrap and unwrap as this identity. Key Vault Crypto Officer on the
# apply principal is granted by the pipeline grant-key-vault-roles command, not here.
resource "azurerm_role_assignment" "storage_customer_managed_key" {
  scope                = data.azurerm_key_vault.evals_storage.id
  role_definition_name = "Key Vault Crypto Service Encryption User"
  principal_id         = azurerm_user_assigned_identity.storage_customer_managed_key.principal_id
  # The identity is created in this same apply. Entra has not listed it yet.
  skip_service_principal_aad_check = true
}

# Outputs for the evaluations storage Key Vault bootstrap.

output "key_vault_id" {
  description = "Resource ID of the Key Vault. Send this to the pipeline grant-key-vault-roles run if the name is ever changed."
  value       = azurerm_key_vault.evals_storage.id
}

output "key_vault_uri" {
  description = "Vault URI used for data-plane key create and wrap."
  value       = azurerm_key_vault.evals_storage.vault_uri
}

output "storage_customer_managed_key_versionless_id" {
  description = "Versionless key ID for azurerm_storage_account.customer_managed_key. Empty until create_storage_key is true."
  value       = var.create_storage_key ? azurerm_key_vault_key.evals_storage[0].versionless_id : null
}

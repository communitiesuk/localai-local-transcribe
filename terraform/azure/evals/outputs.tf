# Outputs for the evals blob storage stack.

output "storage_account_name" {
  description = "Name of the evals data storage account."
  value       = azurerm_storage_account.evals.name
}

output "storage_account_id" {
  description = "Resource ID of the evals data storage account."
  value       = azurerm_storage_account.evals.id
}

output "container_names" {
  description = "Names of the provisioned blob containers."
  value = [
    azurerm_storage_container.input.name,
    azurerm_storage_container.debug.name,
    azurerm_storage_container.output.name,
  ]
}

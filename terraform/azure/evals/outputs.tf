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

output "pipeline_identity_client_id" {
  description = "Client ID of the pipeline managed identity. Use as the Service Principal Id when creating the Azure DevOps service connection."
  value       = azurerm_user_assigned_identity.pipeline.client_id
}

output "pipeline_identity_principal_id" {
  description = "Principal (object) ID of the pipeline managed identity."
  value       = azurerm_user_assigned_identity.pipeline.principal_id
}

output "storage_account_blob_endpoint" {
  description = "Blob endpoint for AZURE_EVALS_STORAGE_ACCOUNT_URL."
  value       = azurerm_storage_account.evals.primary_blob_endpoint
}

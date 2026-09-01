# Outputs for the evals blob storage stack.

output "sensitive_storage_account_name" {
  description = "Name of the account holding the input and debug containers."
  value       = azurerm_storage_account.evals["sensitive"].name
}

output "results_storage_account_name" {
  description = "Name of the account holding the output (results) container."
  value       = azurerm_storage_account.evals["results"].name
}

output "storage_account_ids" {
  description = "Resource IDs of both accounts, keyed by role. Give these to the ADAPT team if they create the private endpoints themselves."
  value       = { for key, account in azurerm_storage_account.evals : key => account.id }
}

output "container_ids" {
  description = "Resource manager IDs of the containers, keyed by container name. These are the scopes the RBAC assignments use."
  value       = { for name, container in azurerm_storage_container.evals : name => container.resource_manager_id }
}

output "private_endpoint_ip_addresses" {
  description = "Private IPs assigned to the blob private endpoints, keyed by account role. Empty when ADAPT owns the endpoints."
  value       = { for key, endpoint in azurerm_private_endpoint.blob : key => endpoint.private_service_connection[0].private_ip_address }
}

output "pipeline_identity_client_id" {
  description = "Client ID of the pipeline managed identity. Use as the Service Principal Id when creating the Azure DevOps service connection."
  value       = azurerm_user_assigned_identity.pipeline.client_id
}

output "pipeline_identity_principal_id" {
  description = "Principal (object) ID of the pipeline managed identity."
  value       = azurerm_user_assigned_identity.pipeline.principal_id
}

output "sensitive_storage_account_blob_endpoint" {
  description = "Blob endpoint for the sensitive account that holds input and debug."
  value       = azurerm_storage_account.evals["sensitive"].primary_blob_endpoint
}

output "results_storage_account_blob_endpoint" {
  description = "Blob endpoint for the results account that holds output."
  value       = azurerm_storage_account.evals["results"].primary_blob_endpoint
}

output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace that receives File and Blob service logs."
  value       = azurerm_log_analytics_workspace.evals.id
}

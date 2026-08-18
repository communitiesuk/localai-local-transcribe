# Outputs for the evals blob storage stack.

output "restricted_storage_account_name" {
  description = "Name of the account holding the input and debug containers."
  value       = azurerm_storage_account.evals["restricted"].name
}

output "shared_storage_account_name" {
  description = "Name of the account holding the output (results) container."
  value       = azurerm_storage_account.evals["shared"].name
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

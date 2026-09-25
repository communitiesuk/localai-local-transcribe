# Resource ID and address of the endpoint. Used when attaching it to the hub zone.

output "private_endpoint_id" {
  description = "Resource ID of the state-account blob private endpoint."
  value       = azurerm_private_endpoint.state_blob.id
}

output "private_endpoint_ip" {
  description = "Private IP address of the state-account blob private endpoint."
  value       = azurerm_private_endpoint.state_blob.private_service_connection[0].private_ip_address
}

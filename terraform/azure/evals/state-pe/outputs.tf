# Values to confirm the endpoint and to give the Azure team if the zone attach needs them.

output "private_endpoint_id" {
  description = "Resource ID of the state-account blob private endpoint."
  value       = azurerm_private_endpoint.state_blob.id
}

output "private_endpoint_ip" {
  description = "Private IP address of the state-account blob private endpoint."
  value       = azurerm_private_endpoint.state_blob.private_service_connection[0].private_ip_address
}

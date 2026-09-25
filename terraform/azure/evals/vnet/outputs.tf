# Values to send the Azure team for the hub-side peering.

output "virtual_network_id" {
  description = "Resource ID of the evaluations virtual network."
  value       = azurerm_virtual_network.evals.id
}

output "virtual_network_name" {
  description = "Name of the evaluations virtual network."
  value       = azurerm_virtual_network.evals.name
}

output "address_space" {
  description = "Address prefixes of the evaluations virtual network."
  value       = azurerm_virtual_network.evals.address_space
}

output "subnet_id" {
  description = "Resource ID of the private-endpoint subnet."
  value       = azurerm_subnet.private_endpoints.id
}

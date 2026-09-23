# Values to confirm the endpoints and to give Nas for the hub zone attach.

output "private_endpoint_ids" {
  description = "Resource IDs of the blob private endpoints, keyed by account role."
  value       = { for key, endpoint in azurerm_private_endpoint.evals_blob : key => endpoint.id }
}

output "private_endpoint_ips" {
  description = "Private IP addresses of the blob private endpoints, keyed by account role."
  value = {
    for key, endpoint in azurerm_private_endpoint.evals_blob :
    key => endpoint.private_service_connection[0].private_ip_address
  }
}

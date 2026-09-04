# Outputs needed to configure the parent stack remote backend.

output "resource_group_name" {
  description = "Resource group that holds the Terraform state storage account."
  value       = azurerm_storage_account.terraform_state.resource_group_name
}

output "storage_account_name" {
  description = "Storage account name for the azurerm backend block."
  value       = azurerm_storage_account.terraform_state.name
}

output "container_name" {
  description = "Blob container that stores Terraform state files."
  value       = azurerm_storage_container.terraform_state.name
}

output "log_analytics_workspace_id" {
  description = "Resource ID of the Log Analytics workspace that receives File service logs from the state account."
  value       = azurerm_log_analytics_workspace.terraform_state.id
}

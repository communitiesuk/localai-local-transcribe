# File service diagnostic logging for both evals storage accounts.
#
# Wiz requires an azurerm_monitor_diagnostic_setting whose target is fileServices on
# azurerm_storage_account.evals. Azure attaches those logs to the File service path, not to
# the storage account ID itself, so the target is each account ID plus /fileServices/default.
#
# The workload only uses blobs. File logging is still enabled because the File service exists
# on a standard account even when no file share has been created. Blob, Queue, and Table
# diagnostic settings are omitted until a Wiz finding asks for them.
#
# This stack creates the Log Analytics workspace so apply does not need a workspace ID in
# terraform.tfvars. The name is law-evals-<environment_name>. If a workspace with that name
# already exists in the resource group, import it rather than creating a second one.

resource "azurerm_log_analytics_workspace" "evals" {
  name                = "law-evals-${var.environment_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    purpose     = "evals-file-service-logs"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_monitor_diagnostic_setting" "evals_file" {
  for_each = azurerm_storage_account.evals

  name                       = "file-service-logging"
  target_resource_id         = "${each.value.id}/fileServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.evals.id

  # Dedicated writes File logs to resource-specific tables in the workspace (StorageFileLogs)
  # rather than the legacy AzureDiagnostics table. Azure Storage requires that destination type.
  log_analytics_destination_type = "Dedicated"

  enabled_log {
    category = "StorageRead"
  }

  enabled_log {
    category = "StorageWrite"
  }

  enabled_log {
    category = "StorageDelete"
  }
}

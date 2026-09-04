# Diagnostic logging for both evals storage accounts.
#
# Wiz required an azurerm_monitor_diagnostic_setting whose target is fileServices on
# azurerm_storage_account.evals. Azure attaches those logs to the service path, not to
# the storage account ID itself, so the File target is each account ID plus
# /fileServices/default.
#
# The workload uses Blob REST (*.blob.core.windows.net), not Azure Files. File logging is
# still enabled because the File service exists on a standard account even when no file
# share has been created. Blob logging records the eval pipeline reads and writes.
# Queue and Table diagnostic settings are omitted until a finding asks for them.
#
# This stack creates the Log Analytics workspace so apply does not need a workspace ID in
# terraform.tfvars. The name is law-evals-<environment_name>. If a workspace with that name
# already exists in the resource group, import it rather than creating a second one.
#
# Public internet ingestion and query are disabled to satisfy Wiz. After apply, logs
# may not reach the workspace and the portal or Cloud Shell cannot query it until Azure
# Monitor private link (AMPLS) exists. This stack does not create that private link.

resource "azurerm_log_analytics_workspace" "evals" {
  name                = "law-evals-${var.environment_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  # Wiz requires both of these false. Azure defaults them to true (public). With them false,
  # diagnostic settings and log queries need Azure Monitor private link, which this stack
  # does not provision. IaC scans pass; live send and query stay blocked until that link exists.
  internet_ingestion_enabled = false
  internet_query_enabled     = false

  tags = {
    purpose     = "evals-storage-logs"
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

resource "azurerm_monitor_diagnostic_setting" "evals_blob" {
  for_each = azurerm_storage_account.evals

  name                       = "blob-service-logging"
  target_resource_id         = "${each.value.id}/blobServices/default"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.evals.id

  # Dedicated writes Blob logs to StorageBlobLogs. This is the table that records eval
  # pipeline access on *.blob.core.windows.net.
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

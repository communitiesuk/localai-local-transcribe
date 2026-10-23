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
# Public internet ingestion and query are disabled to satisfy Wiz. Diagnostic settings
# still deliver logs, because Azure sends them over its own private channel. Queries from
# the portal or the command line need the Azure Monitor private link in monitor.tf.

resource "azurerm_log_analytics_workspace" "evals" {
  name                = "law-evals-${var.environment_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  # Wiz requires both of these false. Azure defaults them to true (public). With them false,
  # log queries need the Azure Monitor private link in monitor.tf. Diagnostic settings are
  # not affected.
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

# Second copy of the same logs for the shared Log Analytics workspace that Cyber can read.
# A diagnostic setting can name only one workspace, so each target has a second setting.
# The project workspace above keeps its copy, so the team has logs it can query itself.
# The shared workspace is in another subscription. The identity that applies this needs
# read and sharedKeys/action on it, otherwise Azure refuses these settings with a 403.
#
# This root also owns the shared settings for the Terraform state account and the vault.
# Those two resources are created by backend/ and key-vault/, whose state lives on test
# ADAPT. A diagnostic setting only points at its target, so this root can create it from
# the target's resource ID. That way the pipeline service principal, which already holds
# the rights on the shared workspace, applies all of the shared copies and no personal
# account needs them. The project workspace settings for those two targets stay in
# backend/ and key-vault/. Do not add a "-shared" setting to either of those roots, or
# two roots would manage the same name.

resource "azurerm_monitor_diagnostic_setting" "evals_file_shared" {
  for_each = azurerm_storage_account.evals

  name                           = "file-service-logging-shared"
  target_resource_id             = "${each.value.id}/fileServices/default"
  log_analytics_workspace_id     = var.shared_log_analytics_workspace_id
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

resource "azurerm_monitor_diagnostic_setting" "evals_blob_shared" {
  for_each = azurerm_storage_account.evals

  name                           = "blob-service-logging-shared"
  target_resource_id             = "${each.value.id}/blobServices/default"
  log_analytics_workspace_id     = var.shared_log_analytics_workspace_id
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

# Resource IDs of the two targets that other roots create. The state account ID is built
# from its name, because the data source for a storage account would add calls that this
# root does not need. Creating a diagnostic setting uses only Azure Resource Manager.
locals {
  terraform_state_storage_account_id = "/subscriptions/${var.subscription_id}/resourceGroups/${var.resource_group_name}/providers/Microsoft.Storage/storageAccounts/${var.terraform_state_storage_account_name}"
}

resource "azurerm_monitor_diagnostic_setting" "terraform_state_file_shared" {
  name                           = "file-service-logging-shared"
  target_resource_id             = "${local.terraform_state_storage_account_id}/fileServices/default"
  log_analytics_workspace_id     = var.shared_log_analytics_workspace_id
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

resource "azurerm_monitor_diagnostic_setting" "terraform_state_blob_shared" {
  name                           = "blob-service-logging-shared"
  target_resource_id             = "${local.terraform_state_storage_account_id}/blobServices/default"
  log_analytics_workspace_id     = var.shared_log_analytics_workspace_id
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

# The vault is found by the data source in storage_customer_managed_key.tf.
resource "azurerm_monitor_diagnostic_setting" "evals_storage_vault_shared" {
  name                       = "key-vault-audit-logging-shared"
  target_resource_id         = data.azurerm_key_vault.evals_storage.id
  log_analytics_workspace_id = var.shared_log_analytics_workspace_id

  # Matches the project workspace setting in key-vault/main.tf, so both copies hold the same categories.
  enabled_log {
    category_group = "allLogs"
  }
}

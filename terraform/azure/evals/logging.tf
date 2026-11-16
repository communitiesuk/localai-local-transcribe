# Diagnostic logging for the evals storage accounts, the Terraform state account, and the vault.
#
# Wiz required an azurerm_monitor_diagnostic_setting whose target is fileServices on each
# storage account. Azure attaches those logs to the service path, not to the storage account
# ID itself, so the File target is each account ID plus /fileServices/default.
#
# The workload uses Blob REST (*.blob.core.windows.net), not Azure Files. File logging is
# still enabled because the File service exists on a standard account even when no file
# share has been created. Blob logging records the eval pipeline reads and writes.
# Queue and Table diagnostic settings are omitted until a finding asks for them.
#
# Every setting sends only to the shared Log Analytics workspace that Cyber reads and that
# the team queries from outside test ADAPT. A diagnostic setting can name only one
# workspace. The shared workspace is in another subscription. The identity that applies
# this needs read and sharedKeys/action on it, otherwise Azure refuses these settings with
# a 403. The pipeline service principal already holds those rights.
#
# This root also owns the settings for the Terraform state account and the vault. Those
# two resources are created by backend/ and key-vault/, whose state lives on test ADAPT.
# A diagnostic setting only points at its target, so this root can create it from the
# target's resource ID. Do not add a logging setting to either of those roots, or two
# roots would manage the same name.
#
# The setting names end in -shared. Renaming them would delete and recreate the settings
# and leave a gap in delivery, so the names stay.
#
# Azure delivers diagnostic logs over its own private channel. No Azure Monitor private
# link is required for delivery.
#
# Dedicated on every storage setting in this file stores Blob and File rows in their own
# tables. Azure Storage requires that destination type. A later plan can show this value
# being set again, because Azure does not report it back.

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

# The state account is created by backend/, so this root builds its resource ID from the
# account name. A storage account data source would call the blob endpoint, which this
# root does not need. The vault ID comes from the data source in storage_customer_managed_key.tf.
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

  # The allLogs group covers every log category the vault offers, which is what Wiz checks for.
  enabled_log {
    category_group = "allLogs"
  }
}

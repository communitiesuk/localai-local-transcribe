# Data plane RBAC, scoped to individual containers rather than the storage account so that
# holding a role on one container grants nothing on the others.
#
# Network access alone is not sufficient: with shared_access_key_enabled = false every call
# needs an Entra ID token, and these assignments are the only thing that makes such a token
# useful. Nothing here grants a role at account, resource group, or subscription scope.
#
# Roles used:
#   Storage Blob Data Reader      - read and list blobs
#   Storage Blob Data Contributor - read, write, and delete blobs
#
# Deliberately not granted anywhere: Owner, Contributor, and Storage Account Contributor.
# Those are control plane roles that could otherwise be used to relax the firewall or
# re-enable shared keys. Keep them off this resource group.

locals {
  # Azure DevOps: reads test data from input, writes debug artefacts and results. Azure has no
  # write-only blob role, so writing debug and output necessarily grants read there too.
  pipeline_grants = {
    input  = "Storage Blob Data Reader"
    debug  = "Storage Blob Data Contributor"
    output = "Storage Blob Data Contributor"
  }

  pipeline_assignments = {
    for container, role in local.pipeline_grants : "pipeline-${container}" => {
      container = container
      role      = role
      principal = var.azure_devops_principal_id
    } if var.azure_devops_principal_id != null
  }

  # Team members. Keep each list to the smallest group that needs the container, and prefer
  # an Entra ID group object ID over a list of individual users.
  team_assignments = merge(
    { for id in var.input_writer_principal_ids : "input-writer-${id}" => {
      container = "input"
      role      = "Storage Blob Data Contributor"
      principal = id
    } },
    { for id in var.debug_reader_principal_ids : "debug-reader-${id}" => {
      container = "debug"
      role      = "Storage Blob Data Reader"
      principal = id
    } },
    { for id in var.results_reader_principal_ids : "results-reader-${id}" => {
      container = "output"
      role      = "Storage Blob Data Reader"
      principal = id
    } },
  )
}

resource "azurerm_role_assignment" "evals" {
  for_each = merge(local.pipeline_assignments, local.team_assignments)

  scope                = azurerm_storage_container.evals[each.value.container].resource_manager_id
  role_definition_name = each.value.role
  principal_id         = each.value.principal
}

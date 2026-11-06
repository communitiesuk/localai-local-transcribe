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
      principal = azurerm_user_assigned_identity.pipeline.principal_id
    }
  }

  # State addresses keep the names from the four previous lists. output was
  # called results in those addresses. A container or role missing from these
  # maps fails the plan here, before Terraform replaces an assignment.
  container_state_name = {
    input  = "input"
    debug  = "debug"
    output = "results"
  }

  role_state_name = {
    "Storage Blob Data Reader"      = "reader"
    "Storage Blob Data Contributor" = "writer"
  }

  # One entry in container_access is one role on one container. Storage Blob Data
  # Contributor already includes read and list, so a writer entry stays off the
  # reader rows. Prefer one Entra ID group object ID per entry.
  team_assignments = {
    for grant in var.container_access :
    "${local.container_state_name[grant.container]}-${local.role_state_name[grant.role]}-${grant.principal_id}" => {
      container = grant.container
      role      = grant.role
      principal = grant.principal_id
    }
  }
}

resource "azurerm_role_assignment" "evals" {
  for_each = merge(local.pipeline_assignments, local.team_assignments)

  scope                = azurerm_storage_container.evals[each.value.container].resource_manager_id
  role_definition_name = each.value.role
  principal_id         = each.value.principal
}

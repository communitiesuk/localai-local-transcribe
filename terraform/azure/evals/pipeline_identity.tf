# User-assigned managed identity the Azure DevOps summarisation pipeline federates to, plus its
# data-plane role on the evals storage account. Used instead of an Entra app registration because the
# tenant blocks app creation. Auth to blobs is Entra ID (workload identity federation) — no keys.
#
# Two-step apply: the federated credential needs the Issuer and Subject that Azure DevOps generates
# when you create the (manual) service connection. First apply creates the identity and role and
# outputs pipeline_identity_client_id; create the ADO connection with that client id; then set
# ado_federation_issuer / ado_federation_subject and apply again to add the federated credential.

resource "azurerm_user_assigned_identity" "pipeline" {
  name                = var.pipeline_identity_name
  resource_group_name = var.resource_group_name
  location            = var.location

  tags = {
    purpose     = "evals-summarisation-pipeline"
    workload    = "evals"
    environment = var.environment_name
  }
}

resource "azurerm_role_assignment" "pipeline_blob" {
  scope                = azurerm_storage_account.evals.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_user_assigned_identity.pipeline.principal_id
}

resource "azurerm_federated_identity_credential" "ado" {
  count = var.ado_federation_issuer != null && var.ado_federation_subject != null ? 1 : 0

  name                = "evals-blob-ado"
  resource_group_name = var.resource_group_name
  parent_id           = azurerm_user_assigned_identity.pipeline.id
  audience            = ["api://AzureADTokenExchange"]
  issuer              = var.ado_federation_issuer
  subject             = var.ado_federation_subject
}

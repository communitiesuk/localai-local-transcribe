# Azure Monitor private link for querying the evals logs (AIILG-1157).
#
# Both project workspaces have public query turned off, so nobody can read them until a
# private route exists. This file creates an Azure Monitor Private Link Scope (AMPLS) that
# holds both workspaces, and one private endpoint for that scope in the evals subnet.
# Resource logs sent by diagnostic settings do not use this route. Azure delivers them over
# its own private channel whatever the workspace public settings say. This route is only
# for people and tools that query the workspaces.
#
# Domain Name System is not in this root. This subscription cannot write the hub Azure
# Monitor private zones. After the endpoint exists, the Azure team attaches it to those zones
# and Zscaler maps the query names. The monitor_private_endpoint_dns_names output lists the
# exact names and addresses to give them. The subnet network security group in vnet/ needs an
# allow for the addresses in the monitor_private_endpoint_ip_addresses output.
#
# The workspace for the state account is created by backend/ with local state. This root
# only reads it, so the scope can include it without managing it.
#
# Both access modes are Open. The hub zones, once attached, resolve every Azure Monitor name
# to this endpoint for each network linked to them. With PrivateOnly, any other workspace or
# Application Insights resource queried from those networks would be refused. With Open,
# those requests carry on over their public routes, and only the two workspaces here are
# private-only because their own public query setting is off.

data "azurerm_log_analytics_workspace" "terraform_state" {
  name                = "law-evals-tfstate-${var.environment_name}"
  resource_group_name = var.resource_group_name
}

resource "azurerm_monitor_private_link_scope" "evals" {
  name                  = "ampls-evals-${var.environment_name}"
  resource_group_name   = var.resource_group_name
  ingestion_access_mode = "Open"
  query_access_mode     = "Open"

  tags = {
    purpose     = "evals-log-queries"
    workload    = "evals"
    environment = var.environment_name
  }
}

locals {
  # Workspaces that the scope covers, keyed by a short role name.
  scoped_workspace_ids = {
    evals           = azurerm_log_analytics_workspace.evals.id
    terraform_state = data.azurerm_log_analytics_workspace.terraform_state.id
  }
}

resource "azurerm_monitor_private_link_scoped_service" "evals" {
  for_each = local.scoped_workspace_ids

  name                = "scoped-${each.key}-${var.environment_name}"
  resource_group_name = var.resource_group_name
  scope_name          = azurerm_monitor_private_link_scope.evals.name
  linked_resource_id  = each.value
}

resource "azurerm_private_endpoint" "monitor" {
  name                = "pe-${azurerm_monitor_private_link_scope.evals.name}-monitor"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "psc-${azurerm_monitor_private_link_scope.evals.name}-monitor"
    private_connection_resource_id = azurerm_monitor_private_link_scope.evals.id
    subresource_names              = ["azuremonitor"]
    is_manual_connection           = false
  }

  tags = {
    purpose     = "evals-log-queries"
    workload    = "evals"
    environment = var.environment_name
  }

  # The Azure team adds the hub DNS zone group outside Terraform. Without this, an apply
  # would remove it and the Azure Monitor names would stop resolving to the private addresses.
  lifecycle {
    ignore_changes = [private_dns_zone_group]
  }

  # The endpoint is created after both workspaces are in the scope so it never exposes an
  # empty scope.
  depends_on = [azurerm_monitor_private_link_scoped_service.evals]
}

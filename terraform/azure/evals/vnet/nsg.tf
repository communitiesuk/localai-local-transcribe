# Network security group for the private endpoint subnet (AIILG-1147).
#
# Apply from test ADAPT with the local state for this root. Do not apply it from an ADO agent.
# ADO means the shared Azure DevOps agents.
#
# Each private endpoint has an inbound allow and a matching outbound allow. Both are TCP port 443.
# The inbound rule lets the callers open HTTPS to that endpoint.
# The outbound rule lets that endpoint open HTTPS to the same callers.
# Once an inbound connection is allowed, Azure permits the reply packets for that connection.
# The outbound rule is the matching rule from the architecture session, for a connection opened by the endpoint.
#
# Callers are the Azure DevOps agent subnets and the test ADAPT connector hosts.
# The connector prefixes, and the prefix for the pool vmss-shared, are set in
# terraform.tfvars on test ADAPT. That file is not committed. The replacement
# pool ado-vmss-latest uses subnet 10.170.128.0/25, which is added in the local
# below. vmss-shared is shut down at 17:00 on 28 October 2026.
# After the deny rules, a test ADAPT blob read succeeded, so that session used one of
# the connector hosts. The read did not show that both hosts were used.
#
# Two deny rules, priority 4000, cover every other inbound and outbound connection.
# Azure checks the allows at 100 to 130 first, so those callers still match.
# The built-in virtual network allow is priority 65000, so the deny is reached before it.
# A caller that is not in the allow list is refused. A wrong connector address cuts off test ADAPT.
#
# The same callers are allowed to every endpoint, including the state account. A later
# results-only route has to add its source on the results rules only.
#
locals {
  # Subnet of the replacement self-hosted agent pool ado-vmss-latest in test.
  # The production pool uses 10.140.82.0/25 and is not a caller of this test network.
  # distinct() keeps one copy if this prefix is later written into terraform.tfvars as well.
  ado_vmss_latest_subnet_prefix = "10.170.128.0/25"

  # Prefixes that may open TCP port 443 to the private endpoints. Each agent
  # has its own address inside its pool prefix. A connector host rebuilt with a new
  # address is no longer covered until the variable is updated. The vmss-shared
  # prefix stays in the variable until that pool is shut down, so both pools work
  # during the changeover.
  allowed_caller_address_prefixes = distinct(concat(
    var.allowed_caller_address_prefixes,
    [local.ado_vmss_latest_subnet_prefix],
  ))

  # Private addresses of each endpoint. Priority is unique within a direction.
  # The same number is used for the inbound and outbound rule of one endpoint.
  # Gaps of 10 leave room to insert another allow. The deny rules use a higher
  # number so these allows are checked first.
  private_endpoint_targets = {
    state = {
      address_prefixes = [var.private_endpoint_address_prefixes.state]
      priority         = 100
    }
    results = {
      address_prefixes = [var.private_endpoint_address_prefixes.results]
      priority         = 110
    }
    sensitive = {
      address_prefixes = [var.private_endpoint_address_prefixes.sensitive]
      priority         = 120
    }
    vault = {
      address_prefixes = [var.private_endpoint_address_prefixes.vault]
      priority         = 130
    }
  }

  # One inbound rule and one outbound rule per endpoint. The outbound rule swaps the two sides.
  private_endpoint_security_rules = merge([
    for endpoint_name, endpoint in local.private_endpoint_targets : {
      "${endpoint_name}-inbound" = {
        name                         = "allow-${endpoint_name}-inbound"
        description                  = "Allow ADO agents and test ADAPT connectors to reach the ${endpoint_name} private endpoint on HTTPS."
        priority                     = endpoint.priority
        direction                    = "Inbound"
        source_address_prefixes      = local.allowed_caller_address_prefixes
        destination_address_prefixes = endpoint.address_prefixes
      }
      "${endpoint_name}-outbound" = {
        name                         = "allow-${endpoint_name}-outbound"
        description                  = "Allow the ${endpoint_name} private endpoint to reach ADO agents and test ADAPT connectors on HTTPS."
        priority                     = endpoint.priority
        direction                    = "Outbound"
        source_address_prefixes      = endpoint.address_prefixes
        destination_address_prefixes = local.allowed_caller_address_prefixes
      }
    }
  ]...)
}

resource "azurerm_network_security_group" "private_endpoints" {
  name                = "nsg-tst-uks-aielt-pe-001"
  location            = var.location
  resource_group_name = var.resource_group_name

  # The rules are written inside the group so one apply sends them in a single update.
  # Separate rule resources would update this group at the same time, and Azure often rejects that.
  dynamic "security_rule" {
    for_each = local.private_endpoint_security_rules
    content {
      name                         = security_rule.value.name
      description                  = security_rule.value.description
      priority                     = security_rule.value.priority
      direction                    = security_rule.value.direction
      access                       = "Allow"
      protocol                     = "Tcp"
      source_port_range            = "*"
      destination_port_range       = "443"
      source_address_prefixes      = security_rule.value.source_address_prefixes
      destination_address_prefixes = security_rule.value.destination_address_prefixes
    }
  }

  # Priority 4000 is checked after the allows at 100 to 130 and before Azure's built-in
  # virtual network allow at 65000. Any protocol and any port, so traffic on a port
  # other than 443 is denied here, ahead of that built-in allow.
  security_rule {
    name                       = "deny-all-inbound"
    description                = "Deny all other inbound traffic to the private endpoint subnet."
    priority                   = 4000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "deny-all-outbound"
    description                = "Deny all other outbound traffic from the private endpoint subnet."
    priority                   = 4000
    direction                  = "Outbound"
    access                     = "Deny"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "*"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    purpose     = "evals-private-endpoints"
    workload    = "evals"
    environment = var.environment_name
  }
}

# Attaching the group is what makes Azure evaluate it for the subnet.
# Private endpoint traffic only starts using it once private_endpoint_network_policies is Enabled.
resource "azurerm_subnet_network_security_group_association" "private_endpoints" {
  subnet_id                 = azurerm_subnet.private_endpoints.id
  network_security_group_id = azurerm_network_security_group.private_endpoints.id
}

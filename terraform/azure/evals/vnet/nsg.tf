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
# Callers are the ADO agent subnet 10.120.1.0/24, measured on 19 October 2026 from agent
# ado-sh-shared0006LR, and the test ADAPT connector addresses 10.20.3.15 and 10.20.3.16.
# The connector addresses are not confirmed.
#
# This group has no deny rule. Azure still applies its built-in virtual network allow, so other
# callers can reach the endpoints after this apply. The deny comes in a later change, once these
# allows have been checked from an ADO agent and from a test ADAPT session.
#
# The same callers are allowed to every endpoint, including the state account. A later
# results-only route has to add its source on the results rules only.

locals {
  # Addresses that may talk to the private endpoints.
  # 10.120.1.0/24 is the whole ADO agent subnet. The scale set gives each agent its own address in that subnet.
  # The two single addresses are connector machines. A rebuilt connector with a new address would miss these rules.
  allowed_caller_address_prefixes = [
    "10.120.1.0/24",
    "10.20.3.15/32",
    "10.20.3.16/32",
  ]

  # Private addresses of the four endpoints on snet-tst-uks-aielt-pe-001.
  # Priority is unique within a direction. The same number is used for the inbound and outbound rule of one endpoint.
  # Gaps of 10 leave room to insert another allow. A later deny uses a higher number so these allows are checked first.
  private_endpoint_targets = {
    state = {
      address_prefix = "10.170.122.4/32"
      priority       = 100
    }
    results = {
      address_prefix = "10.170.122.5/32"
      priority       = 110
    }
    sensitive = {
      address_prefix = "10.170.122.6/32"
      priority       = 120
    }
    vault = {
      address_prefix = "10.170.122.7/32"
      priority       = 130
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
        destination_address_prefixes = [endpoint.address_prefix]
      }
      "${endpoint_name}-outbound" = {
        name                         = "allow-${endpoint_name}-outbound"
        description                  = "Allow the ${endpoint_name} private endpoint to reach ADO agents and test ADAPT connectors on HTTPS."
        priority                     = endpoint.priority
        direction                    = "Outbound"
        source_address_prefixes      = [endpoint.address_prefix]
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

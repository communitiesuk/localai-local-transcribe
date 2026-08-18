# Azure Terraform for evals blob storage (AIILG-644, AIILG-649)

Provisions two storage accounts holding three private blob containers for pipeline data:

| Container | Account      | Purpose metadata | Reachable from            |
| --------- | ------------ | ---------------- | ------------------------- |
| `input`   | restricted   | `purpose=input`  | ADAPT only                |
| `debug`   | restricted   | `purpose=debug`  | ADAPT only                |
| `output`  | shared       | `purpose=output` | ADAPT and MHCLG devices   |

## Why two accounts

Azure storage firewall rules — IP allowlists and private endpoints — are scoped to the storage account, not the container. AIILG-649 requires `input` and `debug` to be unreachable from MHCLG devices while `output` stays readable from them, at the network layer. A single account cannot express that, so the containers are split across two accounts that differ only in their IP allowlist.

## Controls

| Control                                        | Where                                          |
| ---------------------------------------------- | ---------------------------------------------- |
| Deny by default, explicit IP allowlists        | `network_rules` in `main.tf`                   |
| Private endpoint for ADAPT                     | `network.tf`                                   |
| Shared access keys disabled                    | `shared_access_key_enabled = false`, `main.tf` |
| Entra ID required for all data plane calls     | Follows from disabling shared keys             |
| Per-container RBAC, least privilege            | `rbac.tf`                                      |
| No public blobs, no local users, SAS expiry cap | `main.tf`                                      |
| Versioning, blob and container soft delete      | `main.tf`                                      |

Disabling shared access keys is what closes the Azure console bypass: with no account keys there is no account SAS and no "Access key" auth in the portal blob browser, so every read and write is an Entra ID call subject to the role assignments. This holds only while nobody has Owner, Contributor, or Storage Account Contributor on the resource group — those roles can re-enable keys. Keep them off it.

Deployment is manual. There is no pipeline for this stack yet.

## Layout

| Path               | Role                                                               |
| ------------------ | ------------------------------------------------------------------ |
| `backend/`         | One-time bootstrap of remote Terraform state storage               |
| `main.tf`          | Both storage accounts, the three containers, firewall rules        |
| `network.tf`       | Blob private endpoints                                             |
| `rbac.tf`          | Container-scoped role assignments                                  |
| `variables.tf`     | Input variables (required values plus optional hardening defaults) |
| `ACCESS_TESTS.md`  | Access matrix and the test scenarios a reviewer must run           |
| `*.tfvars.example` | Example variable files; copy to `terraform.tfvars` locally         |

## Unknowns left as variables

ADAPT and MHCLG egress addresses, the private endpoint subnet, the private DNS zones, and every principal ID are not known yet. All default to empty or null, which denies the corresponding route. Applying with the defaults gives two accounts nobody can reach on the data plane — safe, and not yet useful. Fill them in as the values are confirmed.

ZScaler may need a rule so ADAPT traffic to `*.blob.core.windows.net` actually egresses from the addresses in `adapt_ip_rules` rather than a shared proxy pool. Confirm the observed source IP with the ADAPT team before trusting the allowlist. If the private endpoint is in place and `restricted_public_network_access_enabled` is false, the restricted account does not depend on egress IPs at all, which is the more robust end state.

## Private endpoint ownership

Where the endpoint is created depends on where the ADAPT VNet lives.

- Same subscription as this stack: set `private_endpoint_subnet_id` and Terraform creates both endpoints.
- ADAPT-owned subscription or tenant: leave `private_endpoint_subnet_id` null. Give the ADAPT team the `storage_account_ids` output; they create the endpoints in their VNet, and we approve the pending connections in the portal under Networking → Private endpoint connections, or with `az network private-endpoint-connection approve`.

Either way the endpoint only resolves privately once `privatelink.blob.core.windows.net` is linked to the ADAPT VNet. Pass `private_dns_zone_ids` if we own the zone; otherwise ask ADAPT to add the A records.

## Softwire Sandbox vs assured Azure environment

| Topic                                                | Transferable as-is | Must adapt later                                        | Uncertain until assured env exists          |
| ---------------------------------------------------- | ------------------ | ------------------------------------------------------- | ------------------------------------------- |
| Two-account split and container names                | Yes                | Names only if platform mandates a prefix                | Whether metadata is required beyond names   |
| Storage account shape (Standard, private containers) | Yes                | Replication via `account_replication_type`              | Final SKU and region                        |
| Firewall, key disablement, SAS expiry, versioning    | Yes                | Retention days and SAS period if platform mandates other | Whether platform policy also enforces these |
| Private endpoint shape                               | Yes                | Subnet, DNS zones, and who creates the endpoint         | Whether ADAPT owns the VNet                 |
| RBAC role choices and container scoping              | Yes                | Every principal ID                                      | Whether groups exist to assign to           |
| Remote state via `azurerm` backend                   | Pattern yes        | Resource group, state account name, key                 | Whether state lives in a platform sub       |
| Tenant, subscription, IPs, and variable values       | No                 | Always                                                  | Naming convention                           |

Still out of scope: customer-managed keys, diagnostic logging to a SIEM, and loading data into containers.

## Prerequisites

- Access to the target Azure tenant and subscription (Softwire sandbox now; assured Azure environment later, which may be a different tenant)
- An **existing** resource group you are allowed to create storage accounts in
- Azure Cloud Shell (Bash), or Azure CLI plus Terraform on a machine that can reach the subscription
- Three globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one restricted, one shared
- **Storage Blob Data Contributor** on the state storage account (or `tfstate` container) for the identity that runs evals `terraform init` / `plan` / `apply`, because remote state uses Entra ID (`use_azuread_auth=true`)
- **User Access Administrator** (or Owner) on the resource group for the applying identity, because `rbac.tf` creates role assignments

## Migrating from the single-account version

AIILG-644 created one account with all three containers, at the Terraform address `azurerm_storage_account.evals`. This configuration replaces it with `azurerm_storage_account.evals["restricted"]` and `["shared"]`, so a plain `terraform apply` plans to **destroy the existing account and every blob in it**. Soft delete does not help: deleting the account removes the container soft-delete scope with it.

Read the plan before approving it. If it shows a `destroy` of a storage account, stop.

The safe sequence is to detach the old account from state, leaving the real resource untouched for manual review, then apply:

```bash
terraform state rm 'azurerm_storage_account.evals'
terraform state rm 'azurerm_storage_container.input'
terraform state rm 'azurerm_storage_container.debug'
terraform state rm 'azurerm_storage_container.output'

terraform plan   # must now show creates only, no destroys
terraform apply
```

Copy any data across with `az storage blob copy start-batch` once both accounts exist, then delete the old account by hand when you are satisfied nothing is left on it. In the sandbox nothing of value is stored yet, so deleting it outright is fine.

## Cloud Shell apply (Softwire sandbox)

Cloud Shell is already authenticated as the portal user. Confirm context first:

```bash
az account show
az account list -o table
az group list -o table
```

If you need a different subscription:

```bash
az account set --subscription "<subscription-id-or-name>"
```

Clone the repo. Using git from Cloud Shell:

```bash
cd $HOME
git clone https://github.com/communitiesuk/localai-local-transcribe
cd localai-local-transcribe/terraform/azure/evals
```

If Cloud Shell home storage was reset, clone again and recreate `terraform.tfvars` from the examples. The evals stack remote state still lives in Azure; the backend stack uses local state, so a wiped shell may need `terraform import` of the existing state storage account and `tfstate` container before a further backend apply.

### Step 1: Bootstrap remote state

```bash
cd backend
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: subscription_id, resource_group_name, location,
# storage_account_name (state account), environment_name
nano terraform.tfvars

terraform init
terraform plan
terraform apply
```

Note the outputs: `resource_group_name`, `storage_account_name`, `container_name`.

### Step 2: Apply the evals stack

```bash
cd ..
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: same subscription and resource group, two DIFFERENT
# storage account names for restricted and shared, plus whichever IPs and
# principal IDs are known. Leave the rest commented out.
nano terraform.tfvars

# Prefer a single line in Cloud Shell. Multiline backslashes can fail there.
# use_azuread_auth=true requires Storage Blob Data Contributor on the state storage
# account or tfstate container for the applying identity; without that role, init fails.
terraform init -backend-config="resource_group_name=<from-backend-output>" -backend-config="storage_account_name=<from-backend-output>" -backend-config="container_name=tfstate" -backend-config="key=evals-blob-containers.tfstate" -backend-config="use_azuread_auth=true"

terraform plan
terraform apply
```

Cloud Shell egresses from an unpredictable IP, so blob data plane commands run there are denied once the firewall is on. This does not block Terraform: accounts, containers, and role assignments are all managed through the resource manager API, which the storage firewall does not gate. There is no allowlist entry for the applying machine, by design — read blobs from ADAPT instead. If you must check by hand in the sandbox, add the address to `adapt_ip_rules` so the exemption is visible in the diff, and remove it before running `ACCESS_TESTS.md`.

### Step 3: Verify

```bash
az storage container list --account-name "<restricted-account-name>" --auth-mode login -o table
az storage container list --account-name "<shared-account-name>" --auth-mode login -o table
```

You should see `input` and `debug` on the restricted account, and `output` on the shared one.

Then work through `ACCESS_TESTS.md` and record the outcome of every scenario.

## Assured Azure environment

Run the same Steps 1 to 3 from scratch in the assured tenant and subscription. Sign into that tenant first if it differs from Softwire sandbox. Use new `terraform.tfvars` values, including three new globally unique storage account names, the real ADAPT and MHCLG addresses, and the real principal IDs. The applying identity still needs **Storage Blob Data Contributor** on the state storage for `use_azuread_auth=true`, plus rights to create role assignments.

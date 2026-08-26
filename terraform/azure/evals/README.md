# Azure Terraform for evals blob storage (AIILG-644, AIILG-649)

Provisions two storage accounts holding three private blob containers for pipeline data:

| Container | Account      | Purpose metadata | Reachable from            |
| --------- | ------------ | ---------------- | ------------------------- |
| `input`   | sensitive    | `purpose=input`  | ADAPT only                |
| `debug`   | sensitive    | `purpose=debug`  | ADAPT only                |
| `output`  | results      | `purpose=output` | ADAPT and MHCLG devices   |

## Why two accounts

Azure storage firewall rules — IP allowlists and private endpoints — are scoped to the storage account, not the container. AIILG-649 requires `input` and `debug` to be unreachable from MHCLG devices while `output` stays readable from them, at the network layer. The containers are therefore split across two accounts that differ only in their IP allowlist.

## Controls

| Control                                        | Where                                          |
| ---------------------------------------------- | ---------------------------------------------- |
| Deny by default, explicit IP allowlists        | `network_rules` in `main.tf`                   |
| Private endpoint and private DNS for ADAPT      | `network.tf`                                   |
| Shared access keys disabled                    | `shared_access_key_enabled = false`, `main.tf` |
| Entra ID required for all data plane calls     | Follows from disabling shared keys             |
| Per-container RBAC, least privilege            | `rbac.tf`                                      |
| No public blobs, no local users, SAS expiry cap | `main.tf`                                      |
| Versioning, blob and container soft delete      | `main.tf`                                      |

Disabling shared access keys is what closes the Azure console bypass: with no account keys there is no account SAS and no "Access key" auth in the portal blob browser, so every read and write is an Entra ID call subject to the role assignments. This holds only while nobody has Owner, Contributor, or Storage Account Contributor on the resource group — those roles can re-enable keys. Keep them off it.

Deployment is manual. There is no pipeline for this stack yet.

## Azure DevOps pipeline identity

`pipeline_identity.tf` also provisions the identity the summarisation and bias eval pipelines use to
reach the blobs — a **user-assigned managed identity** federated to an Azure DevOps service
connection. `rbac.tf` grants it container-scoped data-plane roles: reader on `input`, contributor on
`debug`, and contributor on `output`. A managed identity is used rather than an Entra app
registration because the sandbox tenant blocks app creation for most users.

Federation needs the Issuer and Subject that Azure DevOps generates for the service connection, so
apply in two passes:

1. First apply (leave `ado_federation_issuer` / `ado_federation_subject` unset) creates the identity
   and role. Note the `pipeline_identity_client_id` output.
2. Create the ADO service connection (**Workload identity federation (manual)**) using that client id;
   copy its Issuer and Subject into `terraform.tfvars` and apply again to add the federated credential.

Creating the role assignments needs Owner or User Access Administrator on the relevant scope.

## Layout

| Path               | Role                                                               |
| ------------------ | ------------------------------------------------------------------ |
| `backend/`         | One-time bootstrap of remote Terraform state storage               |
| `main.tf`          | Both storage accounts, the three containers, firewall rules        |
| `network.tf`       | Blob private endpoints                                             |
| `rbac.tf`          | Container-scoped role assignments                                  |
| `variables.tf`     | Input variables (required values plus optional hardening defaults) |
| `terraform.tfvars.example` | Example variable file for both Terraform roots             |

## Unknowns left as variables

ADAPT, temporary Azure DevOps, and MHCLG egress addresses, the private endpoint subnet, any existing private DNS zones, and principal IDs are variables. Empty values deny that route except trusted Azure services using strong authentication.

IP allowlists support public IPv4 CIDR ranges. Use plain IPs for single-host entries.

TODO(AIILG-649): Private endpoints are blocked on the new Azure environment; this currently uses storage network IP restrictions instead.

## Private endpoint ownership

Where the endpoint is created depends on where the ADAPT VNet lives.

- Same subscription as this stack: set `private_endpoint_subnet_id` and Terraform creates both endpoints. Also set `private_endpoint_vnet_id` if Terraform should create and link the private DNS zone.
- ADAPT-owned subscription or tenant: leave `private_endpoint_subnet_id` null. Give the ADAPT team the `storage_account_ids` output; they create the endpoints in their VNet, and we approve the pending connections in the portal under Networking → Private endpoint connections, or with `az network private-endpoint-connection approve`.

Either way the endpoint only resolves privately once `privatelink.blob.core.windows.net` is linked to the ADAPT VNet. If this stack creates the endpoint and `private_dns_zone_ids` is empty, it creates and links that private DNS zone automatically using `private_endpoint_vnet_id`. Pass `private_dns_zone_ids` to use an existing platform-managed zone instead. If ADAPT creates the endpoint in its own subscription, ask ADAPT to configure equivalent private DNS records.

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
- Three globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one sensitive, one results
- MHCLG public egress IPs or CIDR ranges for machines that run `terraform init` / `plan` / `apply` against the state backend
- **Storage Blob Data Contributor** on the state storage account (or `tfstate` container) for the identity that runs evals `terraform init` / `plan` / `apply`, because remote state uses Entra ID (`use_azuread_auth=true`)
- **User Access Administrator** (or Owner) on the resource group for the applying identity, because `rbac.tf` creates role assignments

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

If Cloud Shell home storage was reset, clone again and recreate `terraform.tfvars` from the example. The evals stack remote state still lives in Azure; the backend stack uses local state, so a wiped shell may need `terraform import` of the existing state storage account and `tfstate` container before a further backend apply.

Create one local var file for both Terraform roots:

```bash
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: subscription_id, resource_group_name, location,
# environment_name, terraform_state_storage_account_name, storage account names,
# IP allowlists, and principal IDs.
nano terraform.tfvars
```

### Step 1: Bootstrap remote state

```bash
cd backend

terraform init
terraform plan -var-file=../terraform.tfvars
terraform apply -var-file=../terraform.tfvars
```

Note the outputs: `resource_group_name`, `storage_account_name`, `container_name`.

### Step 2: Apply the evals stack

```bash
cd ..

# Prefer a single line in Cloud Shell. Multiline backslashes can fail there.
# use_azuread_auth=true requires Storage Blob Data Contributor on the state storage
# account or tfstate container for the applying identity, and the caller must connect
# from an IP listed in backend/mhclg_ip_rules; without both, init fails.
terraform init -backend-config="resource_group_name=<from-backend-output>" -backend-config="storage_account_name=<from-backend-output>" -backend-config="container_name=tfstate" -backend-config="key=evals-blob-containers.tfstate" -backend-config="use_azuread_auth=true"

terraform plan
terraform apply
```

Cloud Shell egresses from an unpredictable IP, so blob data plane commands run there are denied once the firewall is on. This does not block Terraform: accounts, containers, and role assignments are all managed through the resource manager API, which the storage firewall does not gate. There is no allowlist entry for the applying machine, by design — read blobs from ADAPT instead. If you must check by hand in the sandbox, add the address to `adapt_ip_rules` so the exemption is visible in the diff, and remove it before reviewing access.

### Step 3: Verify

```bash
az storage container list --account-name "<sensitive-account-name>" --auth-mode login -o table
az storage container list --account-name "<results-account-name>" --auth-mode login -o table
```

You should see `input` and `debug` on the sensitive account, and `output` on the results one.

Then review the expected access matrix above: ADAPT should reach `input`, `debug`, and `output`; MHCLG devices should reach only `output`; and identities without the container-scoped RBAC grants should be denied.

## Assured Azure environment

Run the same Steps 1 to 3 from scratch in the assured tenant and subscription. Sign into that tenant first if it differs from Softwire sandbox. Use new `terraform.tfvars` values, including three new globally unique storage account names, the real ADAPT and MHCLG addresses, and the real principal IDs. The applying identity still needs **Storage Blob Data Contributor** on the state storage for `use_azuread_auth=true`, plus rights to create role assignments.

# Azure Terraform for evals blob storage (AIILG-644, AIILG-649)

Provisions two storage accounts holding three private blob containers for pipeline data:

| Container | Account      | Purpose metadata | Reachable from            |
| --------- | ------------ | ---------------- | ------------------------- |
| `input`   | sensitive    | `purpose=input`  | ADAPT only                |
| `debug`   | sensitive    | `purpose=debug`  | ADAPT only                |
| `output`  | results      | `purpose=output` | ADAPT and MHCLG devices   |

## Why two accounts

Azure storage firewall rules and private endpoints are scoped to the storage account, not the container. AIILG-649 requires `input` and `debug` to be unreachable from MHCLG devices while `output` stays readable from them, at the network layer. The containers are therefore split across two accounts that differ only in the private endpoints that reach them.

## Controls

| Control                                        | Where                                          |
| ---------------------------------------------- | ---------------------------------------------- |
| Deny by default, public access off            | `network_rules` in `main.tf`                   |
| Private endpoint and private DNS for ADAPT      | `network.tf`                                   |
| Shared access keys disabled                    | `shared_access_key_enabled = false`, `main.tf` |
| Entra ID required for all data plane calls     | Follows from disabling shared keys             |
| Per-container RBAC, least privilege            | `rbac.tf`                                      |
| No public blobs, no local users, SAS expiry cap | `main.tf`                                      |
| Versioning, blob and container soft delete      | `main.tf`                                      |
| File and Blob diagnostic logs to Log Analytics  | `logging.tf`                                   |
| File and Blob diagnostic logs on the state account | `backend/logging.tf`                        |
| File service SMB 3.1.1, Kerberos, AES-256-GCM   | `share_properties` in `main.tf` and `backend/main.tf` |

Disabling shared access keys is what closes the Azure console bypass: with no account keys there is no account SAS and no "Access key" auth in the portal blob browser, so every read and write is an Entra ID call subject to the role assignments. This holds only while nobody has Owner, Contributor, or Storage Account Contributor on the resource group — those roles can re-enable keys. Keep them off it.

Deployment is manual. There is no pipeline for this stack yet.

## Azure DevOps pipeline identity

`pipeline_identity.tf` also provisions the identity the summarisation and bias eval pipelines use to
reach the blobs — a **user-assigned managed identity** federated to an Azure DevOps service
connection. `rbac.tf` grants it container-scoped data-plane roles: reader on `input`, contributor on
`debug`, and contributor on `output`. A managed identity is used rather than an Entra app
registration because the sandbox tenant blocks app creation for most users.

Federation needs the Issuer and Subject of the Azure DevOps service connection. Both are known before
the connection exists: the Issuer is `https://vstoken.dev.azure.com/<org-guid>` and the Subject is
`sc://<org>/<project>/evals-blob`. So one apply is enough:

1. Set `EVALS_ADO_FEDERATION_ISSUER` and `EVALS_ADO_FEDERATION_SUBJECT` in the variable group, then
   apply. This creates the identity, its roles, and the federated credential. Note the
   `pipeline_identity_client_id` output.
2. Create the ADO service connection `evals-blob` (**App registration or managed identity (manual)**,
   workload identity federation) using that client id. Check that the Issuer and Subject it shows
   match the variable group.

Creating the role assignments needs Owner or User Access Administrator on the relevant scope.

## Customer-managed key

The evals accounts encrypt with a customer-managed key from the vault in `key-vault/`.

- Settle encryption before anyone uploads data. `infrastructure_encryption_enabled` and the Table and
  Queue key type can only be set at create. Changing either replaces the account and deletes its blobs.
- Rotating or replacing the key does not touch the data. Disabling or deleting the key makes the data
  unreadable until the key is restored. Purge protection keeps a deleted key recoverable.
- A first apply can fail to wrap the key with a 403, because the new Key Vault role for
  `evals-storage-key-id` has not taken effect yet. Role assignments can take several minutes to apply
  ([Microsoft documentation](https://learn.microsoft.com/en-us/azure/role-based-access-control/troubleshooting#role-assignment-changes-are-not-being-detected)).
  Wait a few minutes and rerun the apply.

## Layout

| Path               | Role                                                               |
| ------------------ | ------------------------------------------------------------------ |
| `backend/`         | One-time bootstrap of remote Terraform state storage               |
| `backend/logging.tf` | Log Analytics workspace and File and Blob diagnostic settings for state |
| `main.tf`          | Both storage accounts, the three containers, firewall rules        |
| `logging.tf`       | Log Analytics workspace and File and Blob diagnostic settings      |
| `network.tf`       | Blob private endpoints                                             |
| `rbac.tf`          | Container-scoped role assignments                                  |
| `variables.tf`     | Input variables (required values plus optional hardening defaults) |
| `terraform.tfvars.example` | Example variable file for both Terraform roots             |

## Unknowns left as variables

The private endpoint subnet and principal IDs are variables. Empty network values deny that route except trusted Azure services using strong authentication.

## Private endpoints

`network.tf` creates one blob private endpoint per evals account, and one endpoint for the vault in `key-vault/`, in `private_endpoint_subnet_id`, the subnet created by `vnet/`. This root writes no Domain Name System records, because this subscription cannot write the hub `privatelink.blob.core.windows.net` and `privatelink.vaultcore.azure.net` zones. After an endpoint is created, the Azure team attaches it to its zone. Terraform ignores the zone group they add, so an apply does not remove it.

The vault lock-down is in `key-vault/`. Apply it only after the Evals blob access check shows the vault name resolving to the vault endpoint's private address on `vmss-shared`. The parent plan reads the key on every run, and the agents are not a trusted Microsoft service.

## Softwire Sandbox vs assured Azure environment

| Topic                                                | Transferable as-is | Must adapt later                                        | Uncertain until assured env exists          |
| ---------------------------------------------------- | ------------------ | ------------------------------------------------------- | ------------------------------------------- |
| Two-account split and container names                | Yes                | Names only if platform mandates a prefix                | Whether metadata is required beyond names   |
| Storage account shape (Standard, private containers) | Yes                | Replication via `account_replication_type`              | Final SKU and region                        |
| Firewall, key disablement, SAS expiry, versioning    | Yes                | Retention days and SAS period if platform mandates other | Whether platform policy also enforces these |
| Private endpoint shape                               | Yes                | Subnet, DNS zones, and who creates the endpoint         | Whether ADAPT owns the VNet                 |
| RBAC role choices and container scoping              | Yes                | Every principal ID                                      | Whether groups exist to assign to           |
| Remote state via `azurerm` backend                   | Pattern yes        | Resource group, state account name, key                 | Whether state lives in a platform sub       |
| File and Blob diagnostic settings                    | Yes                | Workspace names follow `environment_name`               | Whether platform wants a central workspace  |
| Tenant, subscription, IPs, and variable values       | No                 | Always                                                  | Naming convention                           |

Still out of scope: Queue/Table diagnostic logging, a SIEM, and loading data into containers. File and Blob logs for the evals accounts go to `law-evals-<environment_name>`. File and Blob logs for the state account go to `law-evals-tfstate-<environment_name>`. If either name already exists in the resource group, import it before apply.

## Prerequisites

- Access to the target Azure tenant and subscription (Softwire sandbox now; assured Azure environment later, which may be a different tenant)
- An **existing** resource group you are allowed to create storage accounts in
- Rights for the applying identity to create a Log Analytics workspace and diagnostic settings on the storage accounts
- Azure Cloud Shell (Bash), or Azure CLI plus Terraform on a machine that can reach the subscription
- Three globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one sensitive, one results
- A machine that reaches the state storage account's private endpoint, for `terraform init` / `plan` / `apply` against the state backend
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
# Edit terraform.tfvars: subscription_id, resource_group_name, environment_name,
# private endpoint subnet, principal IDs, and any pipeline federation values.
# Fixed Softwire sandbox names/defaults live in variables.tf and backend/variables.tf.
nano terraform.tfvars
```

Each root declares only the variables it uses. If a local file contains extra values from another root, Terraform ignores them and says so in a warning; `-compact-warnings` reduces that to a single summary line.

### Step 1: Bootstrap remote state

```bash
cd backend

terraform init
terraform plan -compact-warnings -var-file=../terraform.tfvars
terraform apply -compact-warnings -var-file=../terraform.tfvars
```

Note the outputs: `resource_group_name`, `storage_account_name`, `container_name`.

### Step 2: Apply the evals stack

```bash
cd ..

# Prefer a single line in Cloud Shell. Multiline backslashes can fail there.
# use_azuread_auth=true requires Storage Blob Data Contributor on the state storage
# account or tfstate container for the applying identity, and the caller must connect
# through the state account's private endpoint; without both, init fails.
terraform init -backend-config="resource_group_name=group-aiilgazuresandbox-sandbox" -backend-config="storage_account_name=ltevaltf" -backend-config="container_name=tfstate" -backend-config="key=evals-blob-containers.tfstate" -backend-config="use_azuread_auth=true"

terraform plan -compact-warnings
terraform apply -compact-warnings
```

Cloud Shell egresses from an unpredictable IP, so blob data plane commands run there are denied once the firewall is on. This does not block Terraform: accounts, containers, and role assignments are all managed through the resource manager API, which the storage firewall does not gate. Both accounts have public access off, so read blobs from ADAPT or the shared agents instead.

### Step 3: Verify

```bash
az storage container list --account-name "<sensitive-account-name>" --auth-mode login -o table
az storage container list --account-name "<results-account-name>" --auth-mode login -o table
```

You should see `input` and `debug` on the sensitive account, and `output` on the results one.

Then review the expected access matrix above: ADAPT should reach `input`, `debug`, and `output`; MHCLG devices should reach only `output`; and identities without the container-scoped RBAC grants should be denied.

## Assured Azure environment

Run the same Steps 1 to 3 from scratch in the assured tenant and subscription. Sign into that tenant first if it differs from Softwire sandbox. Use new `terraform.tfvars` values, including three new globally unique storage account names, and the real principal IDs. The applying identity still needs **Storage Blob Data Contributor** on the state storage for `use_azuread_auth=true`, plus rights to create role assignments.

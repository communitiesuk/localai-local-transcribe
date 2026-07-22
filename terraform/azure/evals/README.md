# Azure Terraform for evals blob storage (AIILG-644)

Provisions a storage account with three private blob containers for pipeline data:

| Container | Purpose metadata |
| --------- | ---------------- |
| `input`   | `purpose=input`  |
| `debug`   | `purpose=debug`  |
| `output`  | `purpose=output` |

Azure does not support resource tags on blob containers. Names are the primary identity. `purpose` is also set as container metadata. The storage account carries resource tags.

Both the state and evals storage accounts also set low-regret defaults: no public nested items, local users off, portal prefers Entra ID auth, blob versioning, soft delete (14 days), and a SAS expiration policy (7 days). Replication defaults to `LRS` via `account_replication_type`.

Deployment is manual. There is no pipeline for this stack yet.

## Layout

| Path               | Role                                                                 |
| ------------------ | -------------------------------------------------------------------- |
| `backend/`         | One-time bootstrap of remote Terraform state storage                 |
| `main.tf`          | Evals storage account and the three containers                       |
| `variables.tf`     | Input variables (required values plus optional hardening defaults)   |
| `*.tfvars.example` | Example variable files; copy to `terraform.tfvars` locally           |

## Softwire Sandbox vs assured Azure environment

| Topic                                                | Transferable as-is | Must adapt later                                                         | Uncertain until assured env exists                         |
| ---------------------------------------------------- | ------------------ | ------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Three containers `input` / `debug` / `output`        | Yes                | Names only if platform mandates a prefix                                 | Whether metadata is required beyond names                  |
| Storage account shape (Standard, private containers) | Yes                | Tier / replication via `account_replication_type` if policy requires GRS | Final SKU and region                                       |
| Soft delete, SAS expiry, versioning, auth defaults   | Yes                | Retention days / SAS period if platform mandates different values        | Key rotation reminder (not exposed by azurerm yet)         |
| Remote state via `azurerm` backend                   | Pattern yes        | Resource group, state account name, key                                  | Whether state lives in this subscription or a platform one |
| Manual Cloud Shell apply                             | Process yes        | Auth method if Cloud Shell is unavailable                                | Org policy on who may apply                                |
| Tenant, subscription, and variable values            | No                 | Always                                                                   | Naming convention                                          |

Out of scope here: private endpoints, RBAC, network restrictions, blocking shared key access, customer-managed keys, and loading data into containers.

## Prerequisites

- Access to the target Azure tenant and subscription (Softwire sandbox now; assured Azure environment later, which may be a different tenant)
- An **existing** resource group you are allowed to create storage accounts in
- Azure Cloud Shell (Bash), or Azure CLI plus Terraform on a machine that can reach the subscription
- Two globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one for evals data

Optional variables (`account_replication_type`, `soft_delete_retention_days`, `sas_expiration_period`) have defaults and need not appear in `terraform.tfvars` unless you want to override them.

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

### Step 2: Apply the evals containers stack

```bash
cd ..
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: same subscription and resource group.
# A DIFFERENT storage_account_name for evals data
nano terraform.tfvars

# Prefer a single line in Cloud Shell. Multiline backslashes can fail there.
terraform init -backend-config="resource_group_name=<from-backend-output>" -backend-config="storage_account_name=<from-backend-output>" -backend-config="container_name=tfstate" -backend-config="key=evals-blob-containers.tfstate"

terraform plan
terraform apply
```

### Step 3: Verify in the portal or CLI

```bash
az storage container list \
  --account-name "<evals-storage-account-name>" \
  --auth-mode login \
  -o table
```

You should see `input`, `debug`, and `output`.

Confirm account settings under the storage account **Data management** → **Data protection** (versioning, soft delete) and **Settings** → **Configuration** (public access, Entra default, SAS policy) if needed.

## Assured Azure environment

Run the same Steps 1 to 3 from scratch in the assured tenant and subscription. Sign into that tenant first if it differs from Softwire sandbox. Use new `terraform.tfvars` values, including two new globally unique storage account names.

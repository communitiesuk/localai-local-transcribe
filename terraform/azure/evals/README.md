# Azure Terraform for evals blob storage (AIILG-644)

Provisions a storage account with three private blob containers for pipeline data:


| Container | Purpose metadata |
| --------- | ---------------- |
| `input`   | `purpose=input`  |
| `debug`   | `purpose=debug`  |
| `output`  | `purpose=output` |


Azure does not support resource tags on blob containers. Names are the primary identity. `purpose` is also set as container metadata. The storage account carries resource tags.

Deployment is manual. There is no pipeline for this stack yet.

## Layout


| Path               | Role                                                       |
| ------------------ | ---------------------------------------------------------- |
| `backend/`         | One-time bootstrap of remote Terraform state storage       |
| `main.tf`          | Evals storage account and the three containers             |
| `*.tfvars.example` | Example variable files; copy to `terraform.tfvars` locally |




## Softwire Sandbox vs assured Azure environment


| Topic                                                | Transferable as-is | Must adapt later                                                         | Uncertain until assured env exists                         |
| ---------------------------------------------------- | ------------------ | ------------------------------------------------------------------------ | ---------------------------------------------------------- |
| Three containers `input` / `debug` / `output`        | Yes                | Names only if platform mandates a prefix                                 | Whether metadata is required beyond names                  |
| Storage account shape (Standard, private containers) | Yes                | Tier / replication via `account_replication_type` if policy requires GRS | Final SKU and region                                       |
| Soft delete, SAS expiry, versioning                  | Yes                | Retention days / SAS period if platform mandates different values        | Key rotation reminder (not exposed by azurerm yet)         |
| Remote state via `azurerm` backend                   | Pattern yes        | Resource group, state account name, key                                  | Whether state lives in this subscription or a platform one |
| Manual Cloud Shell apply                             | Process yes        | Auth method if Cloud Shell is unavailable                                | Org policy on who may apply                                |
| Variable values (`subscription_id`, names)           | No                 | Always                                                                   | Naming convention                                          |


Out of scope here: private endpoints, RBAC, network restrictions, and loading data into containers. Soft delete and SAS expiry are included as low-regret hardening; geo-redundancy stays `LRS` by default via `account_replication_type`.

## Prerequisites

- Access to the target Azure subscription (Softwire sandbox now, assured Azure environment later)
- An **existing** resource group you are allowed to create storage accounts in
- Azure Cloud Shell (Bash), or Azure CLI plus Terraform on a machine that can reach the subscription
- Two globally unique storage account names (3 to 24 lowercase letters and digits): one for Terraform state, one for evals data



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

## Retargeting to the assured environment

Do not reuse Softwire sandbox state or `terraform.tfvars` against the assured subscription.

1. **Gather assured values first** (for both stacks): subscription ID, resource group, location, two new globally unique storage account names (state + evals data), `environment_name`, and any other vars that differ from Softwire sandbox.
2. **Bootstrap remote state in assured** (repeat Step 1): put the assured values in `backend/terraform.tfvars`, then `init` / `plan` / `apply` there. Use a new state storage account name.
3. **Configure the evals stack**: put the assured values in `terraform/azure/evals/terraform.tfvars` (different storage account name from the state account).
4. **Point evals at the new backend and apply**: from `terraform/azure/evals`, run `terraform init -reconfigure` with `-backend-config` values from step 2 outputs, then `plan` / `apply`.


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


| Topic                                                    | Transferable as-is | Must adapt later                              | Uncertain until assured env exists                         |
| -------------------------------------------------------- | ------------------ | --------------------------------------------- | ---------------------------------------------------------- |
| Three containers `input` / `debug` / `output`            | Yes                | Names only if platform mandates a prefix      | Whether metadata is required beyond names                  |
| Storage account shape (Standard LRS, private containers) | Yes                | Tier / replication if platform policy differs | Final SKU and region                                       |
| Remote state via `azurerm` backend                       | Pattern yes        | Resource group, state account name, key       | Whether state lives in this subscription or a platform one |
| Manual Cloud Shell apply                                 | Process yes        | Auth method if Cloud Shell is unavailable     | Org policy on who may apply                                |
| Variable values (`subscription_id`, names)               | No                 | Always                                        | Naming convention                                          |


Out of scope here: private endpoints, RBAC, network restrictions, retention, and loading data into containers.

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

Clone the repo (or upload the `terraform/azure/evals` folder) into Cloud Shell. Using git from Cloud Shell:

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

1. Repeat Step 1 in the assured subscription or resource group (new state storage account name).
2. Update `terraform.tfvars` for the evals stack with assured values.
3. Run `terraform init -reconfigure` with the new `-backend-config` values, then `plan` / `apply`.


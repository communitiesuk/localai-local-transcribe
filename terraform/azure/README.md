# Azure evals blob storage — end-to-end setup

The summarisation eval reads input from and writes output to three blob containers
(`input` / `debug` / `output`), authenticated with Entra ID — no account keys. This is the whole
process, start to finish. Detailed reference: [`evals/README.md`](./evals/README.md) (Terraform
stack) and [`../../evals/README.md`](../../evals/README.md) (running the eval).

Replace the placeholders below with your environment's values: `<subscription-id>`,
`<resource-group>`, and `<account>` (the evals data storage account).

## 1. Deploy the storage (Terraform)

Two stacks under `terraform/azure/evals/`: `backend/` bootstraps remote state; the root stack creates
the storage account, the three containers, and the Azure DevOps pipeline identity.

```bash
cd terraform/azure/evals
# state backend (once) — see evals/README.md Step 1 if not yet created
cd backend && terraform init && terraform apply && cd ..

# main stack — init points at the tfstate container (needs Storage Blob Data Contributor on the state account)
terraform init \
  -backend-config="resource_group_name=<state-rg>" \
  -backend-config="storage_account_name=<state-account>" \
  -backend-config="container_name=tfstate" \
  -backend-config="key=evals-blob-containers.tfstate" \
  -backend-config="use_azuread_auth=true"

cp terraform.tfvars.example terraform.tfvars   # edit to match the deployed account
terraform plan     # expect only additions + no destroys
terraform apply
```

`terraform.tfvars` must match the live account or `plan` will try to replace it:

```hcl
subscription_id      = "<your-subscription-id>"
resource_group_name  = "<resource-group>"
location             = "uksouth"
storage_account_name = "<account>"
environment_name     = "sandbox"
```

## 2. Upload synthetic input data

```bash
az login   # your identity needs Storage Blob Data Contributor on the data account
az storage blob upload-batch --account-name <account> --auth-mode login \
  --destination input --destination-path summarisation --source evals/summarisation/sample_data
```

## 3. Run locally

```bash
export AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL="https://<restricted-account>.blob.core.windows.net"
export AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL="https://<shared-account>.blob.core.windows.net"
poetry run python -m evals.summarisation.src.main --config evals/summarisation/configs/blob-smoke-test.yaml
```

Outputs land in `debug/summarisation/standard/<run_id>/` (per-entry) and
`output/summarisation/standard/<run_id>/summary.json` (aggregated).

## 4. Connect Azure DevOps

Auth uses the managed identity from step 1 (a user-assigned identity, because the tenant blocks app
registrations). Wire it to a service connection in two Terraform passes:

1. Get the identity's client id: `terraform output pipeline_identity_client_id`.
2. ADO → **Project settings** → **Service connections** → **New** → **Azure Resource Manager** →
   **Workload identity federation (manual)**. Name it `evals-blob`; enter subscription, tenant, and
   the client id as **Service Principal Id**. Copy the **Issuer** and **Subject** it shows.
3. Put them in `terraform.tfvars` and apply again:
   ```hcl
   ado_federation_issuer  = "<Issuer>"
   ado_federation_subject = "<Subject>"
   ```
   ```bash
   terraform apply
   ```
4. Back in ADO → **Verify and save**.
5. Pipeline **Summarisation Evals** → **Variables** → add:
   ```text
   AZURE_EVALS_RESTRICTED_STORAGE_ACCOUNT_URL=https://<restricted-account>.blob.core.windows.net
   AZURE_EVALS_SHARED_STORAGE_ACCOUNT_URL=https://<shared-account>.blob.core.windows.net
   ```
6. **Run** the pipeline (manual trigger); approve the connection on first run.

## Permissions cheat-sheet

| Action                                    | Role needed                              |
| ----------------------------------------- | ---------------------------------------- |
| `terraform init` against remote state     | Storage Blob Data Contributor on **state** account |
| Upload data / run eval / pipeline read+write | Storage Blob Data Contributor on **data** account |
| `terraform apply` of the role assignment  | Owner or User Access Administrator on the account |

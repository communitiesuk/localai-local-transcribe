# Azure DevOps pipelines

The pipelines in `pipelines/` run eval smoke tests against blob-backed test configs, and one pipeline applies the evals Azure Terraform:

- `evals-summarisation-smoke-test.yml` runs summarisation evals.
- `evals-bias-smoke-test.yml` runs bias evals.
- `evals-transcription-smoke-test.yml` runs transcription evals.
- `evals-terraform-apply.yml` plans or applies `terraform/azure/evals`. Manual only. Default run is plan.
- `evals-blob-access-check.yml` looks up both evals account names on the shared agent and lists `input`, `debug`, and `output` as the `evals-blob` identity. Manual only.
- `evals-ai-gateway-check.yml` looks up the AI Gateway internal hostname on the shared agent and prints the HTTP status of one call. Manual only.

The summarisation and bias pipelines can be run manually, and both are scheduled for Sundays at 21:00 UTC. Azure DevOps cannot express "every two weeks" in cron, so the weekly schedule uses `templates/fortnightly-schedule-gate-job.yml` to skip off-cycle Sundays.

## Variable group

All eval pipelines reference the `evals-pipeline-config` variable group.

To create it in Azure DevOps:

1. Go to **Pipelines** > **Library** > **Variable groups**.
2. Select **+ Variable group**.
3. Name it `evals-pipeline-config`.
4. Add the variables below, marking only the listed secret values as secret.
5. Select **Save**.

Mandatory values:

| Variable | Example | Secret |
| --- | --- | --- |
| `EVALS_AZURE_SERVICE_CONNECTION` | `evals-blob` | No |
| `EVALS_TERRAFORM_SERVICE_CONNECTION` | `SPN-SP-sub-tst-aielt-001` | No |
| `EVALS_ARM_SUBSCRIPTION_ID` | Azure subscription ID | No |
| `EVALS_RESOURCE_GROUP_NAME` | Resource group name | No |
| `EVALS_STATE_STORAGE_ACCOUNT_NAME` | State storage account name | No |
| `EVALS_ENVIRONMENT_NAME` | `test` | No |
| `EVALS_SENSITIVE_STORAGE_ACCOUNT_NAME` | Sensitive storage account name | No |
| `EVALS_RESULTS_STORAGE_ACCOUNT_NAME` | Results storage account name | No |
| `EVALS_ADAPT_EGRESS_IP` | Virtual desktop egress IPv4 address | No |
| `EVALS_ADO_FEDERATION_ISSUER` | Issuer shown on the `evals-blob` service connection | No |
| `EVALS_ADO_FEDERATION_SUBJECT` | Subject shown on the `evals-blob` service connection | No |
| `EVALS_KEY_VAULT_NAME` | Key Vault holding the storage key. Read only by `grant-key-vault-roles` | No |
| `EVALS_SUPER_USER_OBJECT_ID` | Entra object ID given Key Vault Crypto Officer. Read only by `grant-key-vault-roles` | No |
| `AZURE_EVALS_SENSITIVE_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_EVALS_RESULTS_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_APIM_URL` | APIM endpoint | No |
| `AZURE_APIM_INTERNAL_URL` | `AZURE_APIM_URL` with the gateway's internal hostname. Read only by the AI Gateway check | No |
| `AZURE_APIM_API_VERSION` | APIM API version | No |
| `AZURE_APIM_ACCESS_TOKEN` | Temporary APIM bearer token | Yes |
| `AZURE_APIM_SUBSCRIPTION_KEY` | APIM subscription key | Yes |

Configurable values:

| Variable | Recommended value | Secret |
| --- | --- | --- |
| `EVALS_PYTHON_VERSION` | `3.12` | No |
| `EVALS_POETRY_VERSION` | `2.4.1` | No |
| `EVALS_SCHEDULED_RUNS_ENABLED` | `false` | No |
| `EVALS_FORTNIGHTLY_START_SUNDAY` | `2026-08-30` | No |

These are still variable-group entries, but they are optional. If omitted, `templates/evals-variable-defaults.yml` supplies the recommended values.

Terraform can help find the storage endpoint values after the evals stack has been applied:

```bash
cd terraform/azure/evals
terraform output sensitive_storage_account_blob_endpoint
terraform output results_storage_account_blob_endpoint
```

Use `sensitive_storage_account_blob_endpoint` for `AZURE_EVALS_SENSITIVE_STORAGE_ACCOUNT_URL`, and `results_storage_account_blob_endpoint` for `AZURE_EVALS_RESULTS_STORAGE_ACCOUNT_URL`.

If you need to confirm the remote state backend values:

```bash
cd terraform/azure/evals/backend
terraform output resource_group_name
terraform output storage_account_name
terraform output container_name
```

The Terraform apply pipeline needs the ARM variables above. The blob URL and APIM variables are still required for the eval smoke tests after the storage accounts exist.

These are two different Azure identities. Do not point both variables at the platform service principal.

- `EVALS_TERRAFORM_SERVICE_CONNECTION` is the Azure Resource Manager connection used only to apply Terraform (`SPN-SP-sub-tst-aielt-001`).
- `EVALS_AZURE_SERVICE_CONNECTION` is `evals-blob`, a workload-identity connection to the user-assigned managed identity Terraform creates. That identity only has container-scoped blob roles. Create it after the first apply, using `pipeline_identity_client_id`, as in `terraform/azure/README.md` step 4.

## Scheduled run toggle

Set `EVALS_SCHEDULED_RUNS_ENABLED` in the `evals-pipeline-config` variable group to control scheduled runs:

- `true` enables scheduled fortnightly runs.
- `false` skips scheduled runs.

Manual runs are unaffected by this toggle.

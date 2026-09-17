# Azure DevOps pipelines

The pipelines in `pipelines/` run eval smoke tests against blob-backed test configs, and one pipeline applies the evals Azure Terraform:

- `evals-summarisation-smoke-test.yml` runs summarisation evals.
- `evals-bias-smoke-test.yml` runs bias evals.
- `evals-transcription-smoke-test.yml` runs transcription evals.
- `evals-terraform-apply.yml` plans or applies `terraform/azure/evals` using the project Azure Resource Manager service connection. Manual only. Default run is plan. Choose apply only after the plan is create-only.

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
| `EVALS_ARM_SUBSCRIPTION_ID` | `45ceb5a1-1db2-45e6-bfe7-53f488854a31` | No |
| `EVALS_RESOURCE_GROUP_NAME` | `rg-tst-aielt-001` | No |
| `EVALS_STATE_STORAGE_ACCOUNT_NAME` | `aieltevalstftst001` | No |
| `EVALS_ENVIRONMENT_NAME` | `test` | No |
| `EVALS_SENSITIVE_STORAGE_ACCOUNT_NAME` | `aieltevalsentst001` | No |
| `EVALS_RESULTS_STORAGE_ACCOUNT_NAME` | `aieltevalrestst001` | No |
| `EVALS_ADAPT_EGRESS_IP` | `85.210.30.79` | No |
| `AZURE_EVALS_SENSITIVE_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_EVALS_RESULTS_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_APIM_URL` | APIM endpoint | No |
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

These are two different Azure identities. Do not point both variables at the SPN.

- `EVALS_TERRAFORM_SERVICE_CONNECTION` is the platform service principal (`SPN-SP-sub-tst-aielt-001`). It has Contributor and User Access Administrator so it can apply Terraform and create role assignments. As of 17 September 2026 that Azure DevOps connection does not exist. The apply pipeline will fail until it is created and this team can use it.
- `EVALS_AZURE_SERVICE_CONNECTION` is `evals-blob`, a workload-identity connection to the user-assigned managed identity Terraform creates. That identity only has container-scoped blob roles. Create it after the first apply, using `pipeline_identity_client_id`, as in `terraform/azure/README.md` step 4. The eval smoke tests must keep using this connection. They must not run as the SPN.

## Register the Terraform apply pipeline

1. Pipelines → New pipeline → GitHub → this repository → Existing Azure Pipelines YAML file.
2. Branch `feat/evals-terraform-ado-apply`.
3. Path `.azuredevops/pipelines/evals-terraform-apply.yml`.
4. Save. Do not add a schedule.
5. Run with `terraform_command` = `plan` until the plan is create-only, then run `apply`.

## Scheduled run toggle

Set `EVALS_SCHEDULED_RUNS_ENABLED` in the `evals-pipeline-config` variable group to control scheduled runs:

- `true` enables scheduled fortnightly runs.
- `false` skips scheduled runs.

Manual runs are unaffected by this toggle.

# Azure DevOps pipelines

The pipelines in `pipelines/` run eval smoke tests against blob-backed test configs:

- `evals-summarisation-smoke-test.yml` runs summarisation evals.
- `evals-bias-smoke-test.yml` runs bias evals.
- `evals-transcription-smoke-test.yml` runs transcription evals.

The summarisation and bias pipelines can be run manually, and both are scheduled for Sundays at 21:00 UTC. Azure DevOps cannot express "every two weeks" in cron, so the weekly schedule uses `templates/fortnightly-schedule-gate-job.yml` to skip off-cycle Sundays.

## Variable group

All eval pipelines reference the `evals-pipeline-config` variable group.

To create it in Azure DevOps:

1. Go to **Pipelines** > **Library** > **Variable groups**.
2. Select **+ Variable group**.
3. Name it `evals-pipeline-config`.
4. Add the variables below, marking only the listed secret values as secret.
5. Select **Save**.

| Variable | Example | Secret |
| --- | --- | --- |
| `EVALS_PYTHON_VERSION` | `3.12` | No |
| `EVALS_POETRY_VERSION` | `2.4.1` | No |
| `EVALS_AZURE_SERVICE_CONNECTION` | `evals-blob` | No |
| `EVALS_SCHEDULED_RUNS_ENABLED` | `false` | No |
| `EVALS_FORTNIGHTLY_START_SUNDAY` | `2026-08-30` | No |
| `AZURE_EVALS_SENSITIVE_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_EVALS_RESULTS_STORAGE_ACCOUNT_URL` | Storage account blob endpoint | No |
| `AZURE_APIM_URL` | APIM endpoint | No |
| `AZURE_APIM_API_VERSION` | APIM API version | No |
| `AZURE_APIM_ACCESS_TOKEN` | Temporary APIM bearer token | Yes |
| `AZURE_APIM_SUBSCRIPTION_KEY` | APIM subscription key | Yes |

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

## Scheduled run toggle

Set `EVALS_SCHEDULED_RUNS_ENABLED` in the `evals-pipeline-config` variable group to control scheduled runs:

- `true` enables scheduled fortnightly runs.
- `false` skips scheduled runs.

Manual runs are unaffected by this toggle.

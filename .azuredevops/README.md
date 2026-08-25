# Azure DevOps pipelines

The pipelines in `pipelines/` run eval smoke tests against blob-backed test configs:

- `evals-summarisation-smoke-test.yml` runs summarisation evals.
- `evals-bias-smoke-test.yml` runs bias evals.

Both pipelines can be run manually, and both are scheduled for Sundays at 21:00 UTC. Azure DevOps cannot express "every two weeks" in cron, so the weekly schedule uses `templates/fortnightly-schedule-gate-job.yml` to skip off-cycle Sundays.

## Scheduled run toggle

Set `scheduledRunsEnabled` in each pipeline to control scheduled runs:

```yaml
default: 'true'  # scheduled fortnightly runs enabled
default: 'false' # scheduled runs skipped
```

Manual runs are unaffected by this toggle.

# Analytics events export

Full export of the first-party `analytics_event` and `organisation` tables, with no date filtering - every event type, all dates. Writes `analytics_events.csv` and `organisations.csv` into `reporting/analytics_events/output/`.

## Columns

`analytics_events.csv`: `id, occurred_datetime (UTC), event_type, evaluation_id, organisation_id, recording_id, source_id, edit_type, recording_source, template_id, transcription_id, audio_duration_seconds`. The last five come from `event_metadata` (JSONB) and are blank/null when not captured for a given event type.

`organisations.csv`: `organisation_id, organisation_name`.

## Running

Uses the same database connection settings as `reporting/aggregate_analytics` (`common/database/database_credentials.py`, `POSTGRES_*`, `ENVIRONMENT`). From the repository root, for local Postgres (docker compose), with `POSTGRES_*` in the root `.env`:

```bash
poetry run python -m reporting.analytics_events
```

For an AWS environment, log in first, then use the wrapper. It opens the tunnel (`connect-to-aws-db.sh --tunnel-only`), sets `ENVIRONMENT` (default: `production`), `POSTGRES_*`, `POSTGRES_HOSTADDR`, `POSTGRES_IAM_PORT` and `RDS_CA_BUNDLE_PATH` for the run, then closes the tunnel. Needs the `aws` CLI and `session-manager-plugin`:

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
reporting/analytics_events/run-with-tunnel.sh
```

This exports real user/organisation data (first-party analytics events, not sample data) - treat the output CSVs accordingly and avoid committing them.

## Clearing output

```bash
reporting/analytics_events/clear-output.sh
```

Deletes the contents of `reporting/analytics_events/output/` (the directory itself is left in place).

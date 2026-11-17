# Analytics events export

Full export of the first-party `analytics_event` and `organisation` tables - every event type, from the first event up to the end of the last full UTC day. Writes `analytics_events_<timestamp>.csv` and `organisations_<timestamp>.csv` into `reporting/analytics_events/output/`, where `<timestamp>` is the UTC run time as `YYYY-MM-DD_HH-MM` (shared by both files from the same run).

## Columns

`analytics_events_<timestamp>.csv`: `id, occurred_datetime (UTC), event_type, evaluation_id, organisation_id, recording_id, source_id, event_metadata`.

`event_metadata` is the raw JSONB column serialised as text, blank when the event has no metadata. It is exported whole rather than flattened into a column per key, so keys added to `AnalyticsEventMetadata` (`common/database/postgres_models.py`) show up in the export without a change here. Keys are event-type specific: `audio_duration_seconds`, `edit_type`, `copy_type`, `recording_source`, `transcription_id`, `minute_version_id`, `template_id`, `template_source`.

Note that this replaces the earlier flattened `edit_type, recording_source, template_id, transcription_id, audio_duration_seconds` columns, so anything reading exports from before AIILG-1248 by column position or name needs updating.

`organisations_<timestamp>.csv`: `organisation_id, organisation_name`.

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

# Aggregate analytics

Version-controlled report combining Plausible events with first-party `analytics_event` data. For a reporting period it returns underlying counts and percentages for each measure.

## Configuration

Plausible (Stats API v2) is used for all counts except transcription and summary receipts. Events are filtered by name (`event:name`), so they do not need to be configured as goals. Set these in `reporting/aggregate_analytics/.env` (gitignored; copy `.env.example` in the same folder), or export them in your shell:

```bash
PLAUSIBLE_BASE_URL=https://<plausible-host>
PLAUSIBLE_SITE_ID=<site domain>
PLAUSIBLE_API_KEY=<stats api key>
```

The tool loads `reporting/aggregate_analytics/.env` and then the repository root `.env`, taking only `PLAUSIBLE_*` variables (the root `.env`'s local `AWS_*` placeholders are deliberately ignored so they can't override your AWS login). Variables already exported in your shell take priority, then the package `.env`, then the root `.env`. Keep the Plausible API key out of the root `.env`: docker compose passes that whole file into the app containers.

Postgres: the two first-party measures' counts come from `analytics-event-counts.sql`, run once through SQLAlchemy using the app's own settings and credential providers (`common/database/database_credentials.py`). The database is whichever one `POSTGRES_*` and `ENVIRONMENT` point at, read from the shell or the root `.env` (so run from the repository root):
- `ENVIRONMENT=local` (or `test`): uses `POSTGRES_USER` and `POSTGRES_PASSWORD`.
- Any other `ENVIRONMENT`: generates an IAM auth token from your current AWS CLI session (`POSTGRES_USER`, `AWS_REGION`) and verifies TLS against `RDS_CA_BUNDLE_PATH`.
- `POSTGRES_HOSTADDR` (optional): the address actually connected to, e.g. `127.0.0.1` through a tunnel. `POSTGRES_HOST` must still be the RDS hostname, which is used for the IAM token and TLS verification.
- `POSTGRES_IAM_PORT` (optional): the port the IAM token is generated for (`5432`) when `POSTGRES_PORT` is the tunnel's local port.

## Running

From the repository root. For local Postgres (docker compose), with `POSTGRES_*` in the root `.env`:

```bash
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 --caseload reporting/aggregate_analytics/input/caseload.csv
```

For an AWS environment, log in first, then use the wrapper. It opens the tunnel (`connect-to-aws-db.sh --tunnel-only`), sets `ENVIRONMENT`, `POSTGRES_*` (host and database looked up from RDS, overridable from your shell), `POSTGRES_HOSTADDR`, `POSTGRES_IAM_PORT` and `RDS_CA_BUNDLE_PATH` for that run, runs the report and closes the tunnel. Needs the `aws` CLI and `session-manager-plugin`:

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
reporting/aggregate_analytics/run-with-tunnel.sh --environment development -- --start 2026-09-01 --end 2026-09-30 --caseload reporting/aggregate_analytics/input/caseload.csv
```

Both dates are inclusive (UTC for database counts). `--caseload` is only needed for measures 6 and 7; without it their caseload and percentage are `null`.

By default the report is printed to stdout as JSON. Use `--format` to write it to files instead, under `reporting/aggregate_analytics/output/<start>_to_<end>/` (created if missing), where `<start>_to_<end>` is the reporting period, e.g. `2026-09-01_to_2026-09-30`:

```bash
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 --format json
# writes reporting/aggregate_analytics/output/2026-09-01_to_2026-09-30/report.json

poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 --format csv
# writes one reporting/aggregate_analytics/output/2026-09-01_to_2026-09-30/<measure>.csv file per measure
```

or redirect stdout yourself for JSON (warnings go to stderr so stay out of the file; the directory must already exist):

```bash
mkdir -p reporting/aggregate_analytics/output
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 > reporting/aggregate_analytics/output/september.json
```

JSON output is one entry per measure, each with a list of `rows`:

```json
[
  {"measure": "Audio uploads per live recording start",
   "rows": [{"numerator (audio_upload_complete_from_live_recording)": 120,
             "denominator (live_recording_started)": 150, "percentage": 80.0}]},
  {"measure": "Overall summaries created per month",
   "rows": [{"month": "2026-09", "count": 40}]}
]
```

`percentage` is `null` when the denominator (or caseload) is missing or 0. The `numerator` and `denominator` keys carry the name of the event they count in brackets (for database counts restricted to a recording source, the source follows the event type, e.g. `numerator (TRANSCRIPTION_RECEIVED, live_recording)`).

With `--format csv`, each measure is written as its own file (name derived from the measure, e.g. `audio_uploads_per_live_recording_start.csv`) because different measures have different columns (ratio measures have `numerator (...)`/`denominator (...)`/`percentage`; monthly measures have `month`/`count`; the caseload measures add `organisation_id`/`estimated_caseload`).

## Flags

### Report (`python -m reporting.aggregate_analytics`)

| Flag | Required | Example | Description |
|------|----------|---------|-------------|
| `--start` | Yes | `--start 2026-09-01` | Inclusive start date, `YYYY-MM-DD`. |
| `--end` | Yes | `--end 2026-09-30` | Inclusive end date, `YYYY-MM-DD`. Must not be before `--start`. |
| `--caseload` | No | `--caseload reporting/aggregate_analytics/input/caseload.csv` | CSV of estimated caseload. Only needed for measures 6 and 7; without it their caseload and percentage are `null`. A relative path is resolved from the current directory (the repository root when using the wrapper). |
| `--format` | No | `--format csv` | `json` or `csv`. Writes the report into `reporting/aggregate_analytics/output/<start>_to_<end>/` (created if missing): `json` writes a single `report.json`, `csv` writes one `<measure>.csv` file per measure. Without it the JSON report goes to stdout. |
| `-h`, `--help` | No | `--help` | Show usage. |

### Tunnel wrapper (`run-with-tunnel.sh`)

Wrapper flags come first. Everything after a lone `--` is passed unchanged to the report above.

| Flag | Required | Example | Description |
|------|----------|---------|-------------|
| `--environment` | No (default `development`) | `--environment production` | Environment whose bastion and RDS instance (`<env>-bastion-1`, `<env>-database`) to tunnel to. Also sets `ENVIRONMENT` for the run. |
| `--local-port` | No (default `5433`) | `--local-port 5434` | Local port the tunnel listens on. Becomes `POSTGRES_PORT` for the run. |
| `--` | Yes, to pass report flags | `-- --start 2026-09-01 --end 2026-09-30` | Separator; the report's `--start` and `--end` are required, so in practice always include it. |
| `-h`, `--help` | No | `--help` | Show usage. |

```bash
reporting/aggregate_analytics/run-with-tunnel.sh --environment production --local-port 5434 -- --start 2026-09-01 --end 2026-09-30 --format csv
```

### Tunnel script (`connect-to-aws-db.sh`)

| Flag | Required | Example | Description |
|------|----------|---------|-------------|
| `--environment` | No (default `development`) | `--environment production` | Environment to connect to. |
| `--local-port` | No (default `5433`) | `--local-port 5434` | Local port to forward to. |
| `--tunnel-only` | No | `--tunnel-only` | Open the tunnel and keep it open (Ctrl-C to close) instead of starting `psql`. Used by the wrapper. |
| `-- <psql args>` | No | `-- -c 'select 1'` | Passed straight to `psql` (not used with `--tunnel-only`). |

## Estimated caseload dataset

Externally maintained CSV, one row per organisation and calendar month. Keep it in `reporting/aggregate_analytics/input/` (gitignored, so caseload data isn't committed; create the directory if needed) and pass it with `--caseload reporting/aggregate_analytics/input/caseload.csv`.

```csv
organisation_id,month,estimated_caseload
11111111-1111-1111-1111-111111111111,2026-09,60
```

`organisation_id` matches `analytics_event.organisation_id`; `month` is `YYYY-MM`. Duplicates and malformed months are rejected. Organisations with a caseload estimate but no events still get a row (count 0).

## Measures

Defined in `measures.py`.

| # | Measure | Numerator | Denominator |
|---|---------|-----------|-------------|
| 1 | Audio uploads per live recording start | Plausible `audio_upload_complete_from_live_recording` | Plausible `live_recording_started` |
| 2 | Transcription requests per live recording start | Plausible `transcript_requested_for_live_recording` | Plausible `live_recording_started` |
| 3 | Transcription receipts per live recording start | DB `TRANSCRIPTION_RECEIVED` with `recording_source = live_recording` | Plausible `live_recording_started` |
| 4 | Summary requests per transcript received | Plausible `summary_requested` | DB `TRANSCRIPTION_RECEIVED` (live recording and direct upload) |
| 5 | Summary receipts per transcript received | DB `SUMMARY_RECEIVED` | DB `TRANSCRIPTION_RECEIVED` (live recording and direct upload) |
| 6 | Audio uploads versus estimated organisation caseload | Plausible `audio_upload_complete_from_live_recording` + `audio_upload_complete_from_direct_upload`, per `organisation_id` property and month | Estimated caseload |
| 7 | Summaries versus estimated caseload | DB `SUMMARY_RECEIVED` per organisation and month | Estimated caseload |
| 8 | Overall summaries created per month | DB `SUMMARY_RECEIVED` per month | n/a |

Notes:
- Ratios compare event counts in the period; they are not a per-recording funnel, so a percentage can exceed 100%.
- Measure 3 only counts transcriptions whose recording source was captured; older recordings have none.
- Monthly measures group by UTC calendar month. A range that starts or ends mid-month gives partial counts for those months, so use whole months for measures 6 and 7.
- Only `TRANSCRIPTION_RECEIVED` and `SUMMARY_RECEIVED` come from the database; everything else is a Plausible aggregate count.
- Measure 6 relies on the `organisation_id` custom property sent with the audio upload complete events (`hooks/use-start-transcription.ts`). If the organisation breakdown errors or comes back with only a null organisation, check that the property is allowed in Plausible's site settings (Custom properties). Events without it are keyed to a null organisation.
- Plausible months follow the Plausible site's timezone, whereas database months are UTC.

## Tests

```bash
poetry run pytest tests/reporting
```

# Aggregate analytics

Version-controlled report combining Plausible events with first-party `analytics_event` data. For a reporting period it returns underlying counts and percentages for each measure.

## Configuration

Plausible (Stats API v2) is used for all counts except transcription and summary receipts. Events are filtered by name (`event:name`), so they do not need to be configured as goals. Set these in `reporting/aggregate_analytics/.env` (gitignored; copy `.env.example` in the same folder), or export them in your shell:

```bash
PLAUSIBLE_BASE_URL=https://<plausible-host>
PLAUSIBLE_SITE_ID=<site domain>
PLAUSIBLE_API_KEY=<stats api key>
```

The tool loads `reporting/aggregate_analytics/.env` and then the repository root `.env`, taking only `PLAUSIBLE_*` and `POSTGRES_*` variables (the root `.env`'s local `AWS_*` placeholders are deliberately ignored so they can't override your AWS login). Variables already exported in your shell take priority, then the package `.env`, then the root `.env`. Keep the Plausible API key out of the root `.env`: docker compose passes that whole file into the app containers.

Postgres: the two first-party measures' counts come from `analytics-event-counts.sql`, run once through `psql` (CSV output) as in `reporting/README.md`. This tool does not use the app's database settings.
- `--environment local` (default): runs `psql` against the local Postgres (docker compose). It reads the backend's `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_DB` and `POSTGRES_PASSWORD` variables (the same names as in `.env`) and passes them to `psql` as `PG*`. Unset variables default to the values in `reporting/README.md` (`localhost:5432`, user `postgres`, db `minute_db`, password `insecure`). They can come from the root `.env` or your shell.
- `--environment <name>` (e.g. `development`): runs the same query through `connect-to-aws-db.sh`, which opens the SSM tunnel and IAM-authenticated session. Log in first (`aws sso login --profile <profile>` and `export AWS_PROFILE=<profile>`); needs `psql`, the `aws` CLI and `session-manager-plugin`.

## Running

From the repository root. For an AWS environment, log in to AWS first. The tool starts the tunnel itself via `connect-to-aws-db.sh`, which exits with an error if you aren't authenticated:

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
```

Then run:

```bash
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 --caseload reporting/aggregate_analytics/input/caseload.csv
# against an AWS environment (requires the AWS login above)
poetry run python -m reporting.aggregate_analytics --environment development --start 2026-09-01 --end 2026-09-30 --caseload reporting/aggregate_analytics/input/caseload.csv
```

Both dates are inclusive (UTC for database counts). `--caseload` is only needed for measures 6 and 7; without it their caseload and percentage are `null`.

By default the report is printed to stdout. Either write it with `--output`, which takes a file name and saves it in `reporting/aggregate_analytics/output/` (created if missing):

```bash
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 --output september.json
```

or redirect stdout yourself (warnings go to stderr so stay out of the file; the directory must already exist):

```bash
mkdir -p reporting/aggregate_analytics/output
poetry run python -m reporting.aggregate_analytics --start 2026-09-01 --end 2026-09-30 > reporting/aggregate_analytics/output/september.json
```

Output is JSON, one entry per measure, each with a list of `rows`:

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

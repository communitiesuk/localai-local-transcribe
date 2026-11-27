# Feature flags (AppConfig)

Minimal POC for reading AppConfig feature flag values from the backend:

- In deployed environments (ECS), reads via the `appconfig-agent` sidecar over HTTP.
- Locally, reads `terraform/modules/app_config/feature_flags.json` straight off disk instead - no
  sidecar, AWS credentials, or `APP_CONFIG_*` settings required. Note this reflects your local
  working copy of the file, not necessarily what's actually deployed.

## Usage

A CLI entrypoint is also provided for manual testing without needing to run the full backend:

```bash
poetry run python -m backend.api.feature_flags.main                     # full config JSON
poetry run python -m backend.api.feature_flags.main offline_recordings  # single flag's enabled value
```

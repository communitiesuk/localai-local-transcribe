# Feature flags (AppConfig)

Minimal POC for reading AppConfig feature flag values from the backend:

- In deployed environments (ECS), reads via the `appconfig-agent` sidecar over HTTP.
- Locally, falls back to calling AWS AppConfig directly via `boto3`, picking up credentials from the normal AWS credential chain.

## Local setup

### 1. AWS credentials

Make sure you have a fresh SSO session, and that `AWS_PROFILE` is set:

```bash
aws sso login --profile <your-profile>
export AWS_PROFILE=<your-profile>
```

> **Note:** if `.env` already defines `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
> `AWS_SESSION_TOKEN` (e.g. leftover static/docker-compose credentials), these take precedence
> over `AWS_PROFILE` in boto3's credential chain and will cause an
> `UnrecognizedClientException: The security token included in the request is invalid` error.
> Comment these three out in `.env` so your SSO session is used instead:
>
> ```
> # AWS_ACCESS_KEY_ID=...
> # AWS_SECRET_ACCESS_KEY=...
> # AWS_SESSION_TOKEN=...
> ```

### 2. AppConfig IDs

The backend needs the application, environment, and configuration profile IDs. These aren't
currently exposed as Terraform outputs usable locally, so fetch them directly via the AWS CLI
(replace `development` with `staging`/`production` as needed):

```bash
aws appconfig list-applications --query "Items[?Name=='local-transcribe-app-config-development'].Id" --output text
```

```bash
aws appconfig list-environments --application-id <APPLICATION_ID> --query "Items[?Name=='local-transcribe-app-config-environment-development'].Id" --output text
```

```bash
aws appconfig list-configuration-profiles --application-id <APPLICATION_ID> --query "Items[?Name=='local-transcribe-app-config-profile-development'].Id" --output text
```

Add the resulting IDs to `.env`:

```
APP_CONFIG_APPLICATION_ID=<application id from the first command>
APP_CONFIG_ENVIRONMENT_ID=<environment id from the second command>
APP_CONFIG_CONFIGURATION_PROFILE_ID=<configuration profile id from the third command>
```

## Usage

A CLI entrypoint is also provided for manual testing without needing to run the full backend:

```bash
poetry run python -m backend.api.feature_flags.main                     # full config JSON
poetry run python -m backend.api.feature_flags.main offline_recordings  # single flag's enabled value
```

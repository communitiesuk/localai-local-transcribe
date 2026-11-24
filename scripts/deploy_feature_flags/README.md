# deploy_feature_flags

Reconciles `terraform/modules/app_config/feature_flags.json` against the version currently
deployed to AWS AppConfig, and rolls out a new version if the content has changed. Feature
flags are managed outside Terraform's lifecycle, so this script is the supported way to deploy
changes made to `feature_flags.json`.

Logic:

1. Validate `feature_flags.json` against the `AWS.AppConfig.FeatureFlags` JSON schema
   (`schema.py`), failing fast before touching AWS if it doesn't conform.
2. Read the currently *deployed* hosted configuration version for the environment
   (`list_deployments` + `get_hosted_configuration_version`).
3. Reconcile (structurally compare, ignoring `_createdAt`/`_updatedAt`) it against
   `feature_flags.json`.
4. If they match, exit without making any changes.
5. Otherwise, create a new hosted configuration version from `feature_flags.json` - first
   re-checking that the deployed version hasn't changed since step 2, to avoid clobbering a
   concurrent manual change - then validate the new version against the configuration
   profile's own validators (`validate_configuration`) before starting a deployment of it.

## CI deployment

The script runs as its own job, `deploy-feature-flags`, in `.github/workflows/deploy-base.yml`.

It's independent of the `apply` job: feature-flag-only content changes never
appear in `terraform plan`'s diff (because of `ignore_changes = [configuration_version]`), so
if this only ran as a step inside `apply`, a flag change would silently never deploy whenever
`apply` itself was skipped (e.g. no infrastructure changes). Instead `deploy-feature-flags`:

- `needs: [plan, apply]` and runs with `if: always() && needs.plan.result == 'success'`, so it
  still runs even when `apply` is skipped, and only skips itself if `plan` failed or was
  cancelled.
- Shares the `tfstate-${environment}` concurrency group with `plan`/`apply`, since it reads
  Terraform outputs from the same state.
- Assumes the `github-actions-appconfig-deploy` IAM role, scoped to exactly the AppConfig
  (and KMS) actions this job needs - see `terraform/modules/app_config/iam.tf`'s
  `app_config_deploy` policy.

Steps, in order:

1. **Terraform init** (read-only against the existing state, in `terraform/${environment}`) so
   `terraform output` is available.
2. **Read AppConfig Terraform outputs** - captures `app_config_application_id`,
   `app_config_environment_id`, `app_config_configuration_profile_id` and
   `app_config_deployment_strategy_id` (defined in `terraform/${environment}/outputs.tf`) via
   `terraform output -raw`, as step outputs.
3. **Deploy feature flags to AppConfig** - runs `python -m deploy_feature_flags.main` with
   `working-directory: scripts`, passing the four IDs from step 2 as CLI flags. `--feature-flags-file`
   is left at its default, which resolves to `terraform/modules/app_config/feature_flags.json`
   regardless of working directory.

The step has `id: deploy`, and the job exposes `outputs.status` (`updated` or `no_change`,
written to `$GITHUB_OUTPUT` by the script - see below) so the `notify-slack` job can report
whether a feature flag deployment happened alongside the rest of the pipeline's status.

## CLI deployment

The module has no dependency on the CI runner or its environment - it can be run directly
wherever you have AWS credentials with the required AppConfig permissions
(`appconfig:ListDeployments`, `GetHostedConfigurationVersion`, `CreateHostedConfigurationVersion`,
`ValidateConfiguration`, `StartDeployment`).

Because `main.py` uses relative imports (so it works identically whether run in CI or locally),
it must be run as a module with `scripts/` as the working directory (or otherwise on
`PYTHONPATH`), not invoked directly as a script file:

```bash
cd scripts
poetry run python -m deploy_feature_flags.main \
  --application-id <id> \
  --environment-id <id> \
  --configuration-profile-id <id> \
  --deployment-strategy-id <id> \
  [--feature-flags-file path/to/feature_flags.json]
```

All four IDs are required. Each can be supplied either as a `--flag` or via the matching
environment variable instead (useful for local runs where you don't want to look up IDs by
hand each time):

| Flag | Env var | Default |
|------|---------|---------|
| `--application-id` | `APPCONFIG_APPLICATION_ID` | none - required |
| `--environment-id` | `APPCONFIG_ENVIRONMENT_ID` | none - required |
| `--configuration-profile-id` | `APPCONFIG_CONFIGURATION_PROFILE_ID` | none - required |
| `--deployment-strategy-id` | `APPCONFIG_DEPLOYMENT_STRATEGY_ID` | none - required |
| `--feature-flags-file` | `APPCONFIG_FEATURE_FLAGS_FILE` | `terraform/modules/app_config/feature_flags.json` (repo-root relative) |

### Reading the IDs via Terraform output

Both `terraform output` and the deployment itself need a credentialed AWS session - start one
first if you don't already have one:

```bash
export AWS_PROFILE=<your-profile>
aws sso login --profile <your-profile>
```

The IDs for a given environment can be read from that environment's Terraform state, e.g.:


```bash
cd terraform/<environment>
terraform output -raw app_config_application_id
terraform output -raw app_config_environment_id
terraform output -raw app_config_configuration_profile_id
terraform output -raw app_config_deployment_strategy_id
```

Copying each value into the `--flag`/env var form above is four extra lookups. Since every ID
can be supplied via its env var, and `terraform output -raw` can be pointed at another
environment's directory with `-chdir` (without `cd`-ing there yourself), the lookups and the
deployment can be combined into a single command - no intermediate file needed:

```bash
cd scripts
```

The block below is a single copy-pasteable command - paste it into the terminal as-is once
you're in `scripts/`:

`<environment>` below is a placeholder - replace the whole `<environment>` token with the actual
environment directory name (`development`, `staging`, or `production`) in every command.

```bash
APPCONFIG_APPLICATION_ID=$(terraform -chdir=../terraform/<environment> output -raw app_config_application_id) \
APPCONFIG_ENVIRONMENT_ID=$(terraform -chdir=../terraform/<environment> output -raw app_config_environment_id) \
APPCONFIG_CONFIGURATION_PROFILE_ID=$(terraform -chdir=../terraform/<environment> output -raw app_config_configuration_profile_id) \
APPCONFIG_DEPLOYMENT_STRATEGY_ID=$(terraform -chdir=../terraform/<environment> output -raw app_config_deployment_strategy_id) \
poetry run python -m deploy_feature_flags.main
```

The `cd scripts` is still required (the module needs `scripts/` as the working directory - see
above), but the four `terraform output` calls no longer need their own `cd`: `-chdir` runs them
against `../terraform/<environment>` directly, and their output is captured straight into the
matching env var for the `poetry run` call on the same line. `--feature-flags-file` isn't
involved in this, so it still falls back to its default unless you override it too.

Behaviour is identical to the CI run: if the deployed configuration already matches
`feature_flags.json`, the script logs that there's nothing to do and exits `0` without creating
a new version or starting a deployment. AWS credentials are picked up via boto3's normal
credential chain (environment variables, `~/.aws/credentials` profile, SSO session, etc.) - the
script doesn't configure or assume any role itself.

`write_github_output` (used to report `status=updated`/`status=no_change`) is a no-op outside
GitHub Actions - it only writes if `$GITHUB_OUTPUT` is set, so running the script locally
produces no extra files or errors.

### The `feature_flags.json` file

AWS AppConfig's `AWS.AppConfig.FeatureFlags` format only allows three top-level keys:

```json
{
  "flags": {
    "offline_recordings": {
      "name": "offline_recordings",
      "description": "Offline recordings feature flag"
    }
  },
  "values": {
    "offline_recordings": {
      "enabled": false
    }
  },
  "version": "1"
}
```

- `flags` - one entry per flag, keyed by flag name. `name` must match the key; `description` is
  optional but recommended.
- `values` - one entry per flag (same key), holding its actual setting. `enabled` is required
  for every flag.
- `version` - the schema format version, always `"1"`. This is not a deployment/config version
  number (that's tracked separately by AppConfig itself via `ConfigurationVersion`), so it
  should stay hardcoded and not be bumped manually.

**To add a flag**: add matching entries under both `flags` and `values` with the same key, then
run a CLI deployment (or let CI pick it up) to roll it out.

**To change a flag's state**: edit its `enabled` value under `values` and deploy.

**Retiring a flag**: AppConfig hosted configuration versions are immutable - there's no way to
delete or edit a version once it's been created and deployed. A flag can't be "removed" from
history, only superseded: delete its entries from both `flags` and `values` in
`feature_flags.json` and deploy as normal. This creates and rolls out a new version that simply
doesn't include the retired flag, which then takes effect for all clients once deployed -
earlier versions (still containing the flag) remain in AppConfig's version history, but are no
longer the *deployed* version, so no client refers to them anymore for normal reads. If a
retirement (or any deploy) turns out to be wrong, the same immutability also enables an easy
rollback: start a new deployment of an earlier `ConfigurationVersion` number directly (e.g. via
`aws appconfig start-deployment`), rather than trying to reconstruct the old content by hand.

**Multivariants**: AppConfig also supports per-flag `attributes` (under `flags.<name>`) and
matching custom attribute values (under `values.<name>`), letting a flag carry more than a
plain boolean - for example, a rollout percentage or a string variant:

```json
{
  "flags": {
    "rollout_example": {
      "name": "rollout_example",
      "attributes": {
        "variant": { "constraints": { "type": "string" } }
      }
    }
  },
  "values": {
    "rollout_example": {
      "enabled": true,
      "variant": "beta"
    }
  },
  "version": "1"
}
```

See the [AWS AppConfig feature flag
creation docs](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-and-profile-feature-flags.html)
for the full `attributes`/constraints schema.

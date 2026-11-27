# AWS cost modelling

The scripts in this directory can be used to generate forecast monthly costs for the production AWS environment.

The costs are created by an `infracost` scan against the production terraform combined with a usage model, provided to infracost as a YAML file.

Costs are monthly pre-tax USD, and provided as a baseline cost and then several variant scenarios. The variants are intended to be orthogonal, such that one scenario within each variant group can be selected and added together for a final cost. Costs exclude the price of AWS Shield Advanced, as this is covered an an organisational level.

## Generating a forecast

### Prerequisites

You will need `python3` and `infracost` available. The Infracost CLI must be authenticated. Run the following to authenticate:

```shell
infracost auth login --oauth-use-device-flow
```

### Generation

From the repository root, run:

```shell
python3 terraform/cost-modelling/infracost-forecast.py
```

Pass `--csv forecast.csv` to also save the output to CSV. Pass `--rate-scale-factor <factor>` to apply `<factor>`, a value between 0 and 1, to scale many AWS rates.

Key things to check before regenerating forecasts are:
* The ARM64 Fargate rates in London (see `Controlling variants` below)
* The usage-based scenarios (see `Controlling usage scenarios` below), including the default assumptions

## Controlling variants

Variant scenarios are described by `infracost-forecast.json`.

Terraform variant groups exist for:
* The number of worker tasks (`workers`)
* The number of frontend tasks (`frontend`)
* The number of backend tasks (`backend`)
* The database instance class (`database`) and whether it is multi-AZ or not (`database_multi_az`) - the cartesian product of values specified produce the variant group.

Each value under a variant group that does not match the production terraform causes a variant line to be generated in the output - i.e. a copy of the production terraform files are manipulaed, then `infracost` is run again.

Usage variants are defined by:
* `idle_usage_-_file` - the baseline scenario (with only the usage that would be generated even without any users)
* `usage`, specifying various additional usage profiles (`low`, `medium`, `high`). See below for how the usage profile files are generated.

Infracost currently seems to report x86 prices for Fargate tasks, even when configured to use ARM64. The `fargate_hourly_usd` settings specify the London rates for both architectures. The script accepts either configured rate and recalculates the cost using the task's actual architecture; if the reported rate is already correct, the cost is unchanged. If neither rate matches, the script stops so you can check the configured prices.

## Controlling usage scenarios

Usage variants are controled as described above. To control the scenario files to feed in to those variants, first review/edit `infracost-workload.yml`.

The `defaults` section defines the common high level knobs you can use to tune our usage estimates.

The `scenarios` section defines the different scenarios for which infracost usage files will be generated - i.e. which can then be configured as variants in `infracost-forecast.json`. Each scenario must provide a `monthly_active_users` estimate and can override other settings.

The `assumptions` section defines more detailed tuning nobs, either about the usage patterns we will encounter (e.g. `https_requests_per_meeting`), our implementation (e.g. `converted_audio_kbps`), or AWS (e.g. `free_egress_gb`).

The `resource_type_default_usage` section defines the baseline usage meters for various AWS resources.

To regenerate the usage scenario files, first install the poetry dependencies:

```shell
poetry install --only infracost --no-root
```

Then generate the files:

```shell
poetry run python terraform/cost-modelling/generate-infracost-usage.py
```
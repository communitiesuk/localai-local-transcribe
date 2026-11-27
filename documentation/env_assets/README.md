# Environmental Impact Assessment — Scripts

These scripts generate the numbers in `documentation/env-impact.md`.

## Setup

```bash
cd documentation/env_assets
poetry install
```

## Usage

Run the full report:

```bash
poetry run python calculations.py
```

Run a single section:

```bash
poetry run python transcription.py   # ASR energy + carbon
poetry run python llm_inference.py   # LLM invocation costs
poetry run python training.py        # Model training footprint
poetry run python water.py           # Scope 2 water embedded in electricity
poetry run python comparisons.py     # Real-life analogies
poetry run python aws.py             # AWS carbon data entered manually from the AWS Console
```

The full report, `water.py`, and `aws.py` prompt for the latest month's
market-based and location-based emissions from the AWS Sustainability page.
This is the default so running the scripts does not require command-line access
to production.

To fetch those values with the existing AWS API integration, opt in explicitly:

```bash
poetry run python calculations.py --api_calls
poetry run python water.py --api_calls
poetry run python aws.py --api_calls
```

> [!WARNING]
> `--api_calls` is only for development and staging. **DO NOT use it for
> production.** It requires valid AWS credentials and accesses the configured
> AWS account.

## How it works

- **`assumptions.yaml`** — all hardcoded constants (cited values from papers/specs). Edit this to update assumptions without touching code.
- **`utils.py`** — loads `assumptions.yaml`, initialises EcoLogits, provides shared display helpers.
- Each module has a `display()` function that prints its section; `calculations.py` calls them all.
- EcoLogits-derived values (model params, grid intensity) are fetched at import time — they require a network connection on first run.

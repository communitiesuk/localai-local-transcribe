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
poetry run python aws.py             # Live AWS carbon data (requires AWS CLI + credentials)
```

## How it works

- **`assumptions.yaml`** — all hardcoded constants (cited values from papers/specs). Edit this to update assumptions without touching code.
- **`utils.py`** — loads `assumptions.yaml`, initialises EcoLogits, provides shared display helpers.
- Each module has a `display()` function that prints its section; `calculations.py` calls them all.
- EcoLogits-derived values (model params, grid intensity) are fetched at import time — they require a network connection on first run.

from __future__ import annotations

SENTIMENT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-sentiment-latest"
SENTIMENT_MAX_LENGTH = 512
SENTIMENT_CHUNK_SIZE = 400
SENTIMENT_CHUNK_OVERLAP = 60

RESULTS_FILENAME = "results.jsonl"
SUMMARY_FILENAME = "summary.json"

SPC_BASELINE_FILENAME = "spc_baseline.yaml"

# Number of standard deviations for the control limits (the conventional 3-sigma rule).
SPC_SIGMA = 3.0

# Minimum number of observations needed to derive a control-chart baseline for a metric.
# An "observation" is one *comparison* — a single transcript's factual-vs-counterfactual delta,
# already averaged over that comparison's iterations — pooled across the run. It is NOT a per-iteration
# value and NOT per-group: build_spc_baseline collects one delta per comparison across all comparisons.
# Below two comparisons a mean/standard deviation has no meaning, so the metric is skipped.
MIN_BASELINE_OBSERVATIONS = 2

FOUR_FIFTHS_RATIO = 0.8

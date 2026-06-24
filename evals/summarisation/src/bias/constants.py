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

FOUR_FIFTHS_RATIO = 0.8

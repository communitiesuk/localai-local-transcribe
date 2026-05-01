from pathlib import Path

_DATASET_GEN_DIR = Path(__file__).resolve().parents[2]
CHARACTERISTICS_OUTPUT_DIR = _DATASET_GEN_DIR / "characteristics" / "output"

INPUT_DIR = Path(__file__).resolve().parents[1] / "input"
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"

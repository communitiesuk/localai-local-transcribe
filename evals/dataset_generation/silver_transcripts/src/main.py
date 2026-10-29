"""
Command line entry point for silver transcript generation.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import yaml

from evals.dataset_generation.silver_transcripts.src.config import (
    DEFAULT_CUTOFF_SECONDS,
    SilverTranscriptConfig,
)
from evals.dataset_generation.silver_transcripts.src.pipeline import SilverTranscriptPipeline

logger = logging.getLogger(__name__)
WORKDIR = Path(__file__).resolve().parents[1]
DEFAULT_WORK_DIR = WORKDIR / "output"
DEFAULT_CONFIG = WORKDIR / "configs" / "smoke_test.yaml"


def run_pipeline(
    *,
    input_dir: Path | None = None,
    work_dir: Path | None = None,
    cutoff_seconds: float = DEFAULT_CUTOFF_SECONDS,
) -> int:
    """
    Generates transcripts and segments from local audio.

    Returns a process exit code: 0 for success, 1 when any sample failed to generate.
    work_dir defaults to output/ under this directory.
    """
    pipeline = SilverTranscriptPipeline(work_dir or DEFAULT_WORK_DIR, cutoff_seconds=cutoff_seconds)

    if input_dir is None:
        msg = "input_dir must be specified in the config to generate drafts"
        raise ValueError(msg)

    records = pipeline.generate_transcripts(input_dir)
    for record in records:
        logger.info("%s: %s", record.sample_id, record.status)
    logger.info("Processed %d inputs; review the audio.txt and audio.mp3 files under segments/", len(records))
    return 1 if any(record.status == "failed" for record in records) else 0


def load_config(config_path: Path) -> SilverTranscriptConfig:
    """
    Loads silver transcript configuration from a YAML file.
    """
    return SilverTranscriptConfig.model_validate(yaml.safe_load(config_path.read_text(encoding="utf-8")))


def _resolve_config_path(config_path: Path, value: Path | None) -> Path | None:
    """
    Resolves a directory declared in a config relative to the YAML file that declared it.
    """
    if value is None:
        return None
    return (config_path.parent / value.expanduser()).resolve()


def main() -> None:
    """
    Parses command-line arguments and runs the silver transcript pipeline.
    """
    parser = argparse.ArgumentParser(description="Generates transcripts for annotation.")
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to config file (default: configs/smoke_test.yaml)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    config_path = args.config.expanduser().resolve()
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)

    config = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)

    exit_code = run_pipeline(
        input_dir=_resolve_config_path(config_path, config.input_dir),
        work_dir=_resolve_config_path(config_path, config.work_dir),
        cutoff_seconds=config.cutoff_seconds,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

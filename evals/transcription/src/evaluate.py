from __future__ import annotations

import argparse
import logging
import shutil
import sys
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from common.audio.ffmpeg import get_duration
from common.settings import get_settings
from evals.shared.blob_io import publish_run_outputs, stage_dataset_prefix
from evals.shared.blob_storage import EvalBlobStorage
from evals.transcription.src.adapters.base import ServiceTranscriptionAdapter
from evals.transcription.src.adapters.registry import ADAPTER_REGISTRY
from evals.transcription.src.core.dataset import (
    prepare_audio_for_transcription,
)
from evals.transcription.src.core.dataset_loaders import DATASET_LOADER_REGISTRY
from evals.transcription.src.core.results import save_results, save_summary_results
from evals.transcription.src.core.runner import run_engines_parallel
from evals.transcription.src.drift import apply_drift_thresholds
from evals.transcription.src.models import DatasetProtocol, EvaluationConfig

settings = get_settings()
WORKDIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)

RESULTS_RELATIVE_PATHS = frozenset({"summary.json"})


@dataclass(frozen=True)
class EvaluationRunOutcome:
    exit_code: int
    run_id: str
    run_output_dir: Path
    detailed_results_path: Path
    summary_path: Path


def run_evaluation_with_outputs(
    num_samples: int | None = None,
    sample_duration_fraction: float | None = None,
    prepare_only: bool = False,
    max_workers: int | None = None,
    adapter_names: list[str] | None = None,
    check_drift_thresholds: bool = False,
    *,
    dataset: DatasetProtocol | None = None,
    output_dir: Path | None = None,
    structured_output: bool = False,
) -> EvaluationRunOutcome:
    """Run eval and return output paths."""
    output_root = output_dir if output_dir is not None else WORKDIR / "output"
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    run_id = f"eval_{timestamp}"
    run_output_dir = output_root / run_id if structured_output else output_root
    detailed_results_path = run_output_dir / "results.json"
    if not structured_output:
        detailed_results_path = run_output_dir / f"evaluation_results_{timestamp}.json"
    summary_path = run_output_dir / "summary.json"

    logger.info("Loading dataset...")
    if dataset is None:
        dataset = _load_dataset("ami", None, num_samples, sample_duration_fraction)

    indices = list(range(len(dataset)))
    logger.info("Loaded %d samples from the dataset", len(indices))

    if prepare_only:
        logger.info("=== Dataset Preparation Complete ===")
        logger.info("Prepared %d meetings", len(indices))
        return EvaluationRunOutcome(
            exit_code=0,
            run_id=run_id,
            run_output_dir=run_output_dir,
            detailed_results_path=detailed_results_path,
            summary_path=summary_path,
        )

    if adapter_names is None:
        msg = "adapter_names is required when prepare_only is False"
        raise ValueError(msg)

    adapters = [ServiceTranscriptionAdapter(ADAPTER_REGISTRY[name]) for name in adapter_names]

    logger.info(
        "Running %d adapters in parallel on %d samples...",
        len(adapters),
        len(indices),
    )
    results = run_engines_parallel(
        adapters=adapters,
        indices=indices,
        dataset=dataset,
        wav_write_fn=prepare_audio_for_transcription,
        duration_fn=lambda path: get_duration(Path(path)),
        run_id=run_id,
        timestamp=timestamp,
        dataset_version=dataset.dataset_version,
        dataset_split=dataset.dataset_split,
        max_workers=max_workers,
    )

    save_results(results, detailed_results_path)
    save_summary_results(results, summary_path)

    logger.info("=== Evaluation Complete ===")
    logger.info("Dataset: %s", dataset.dataset_version)
    logger.info("")
    for result in results:
        wer_pct = result.summary.metrics["wer"].mean * 100.0
        logger.info(
            "%s WER: %.2f%%",
            result.summary.engine_version,
            wer_pct,
        )
    logger.info("Results saved to: %s", detailed_results_path)

    exit_code = apply_drift_thresholds(results, run_output_dir, timestamp) if check_drift_thresholds else 0
    return EvaluationRunOutcome(
        exit_code=exit_code,
        run_id=run_id,
        run_output_dir=run_output_dir,
        detailed_results_path=detailed_results_path,
        summary_path=summary_path,
    )


def run_evaluation(
    num_samples: int | None = None,
    sample_duration_fraction: float | None = None,
    prepare_only: bool = False,
    max_workers: int | None = None,
    adapter_names: list[str] | None = None,
    check_drift_thresholds: bool = False,
) -> int:
    """Run eval and return an exit code."""
    return run_evaluation_with_outputs(
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
        prepare_only=prepare_only,
        max_workers=max_workers,
        adapter_names=adapter_names,
        check_drift_thresholds=check_drift_thresholds,
    ).exit_code


def load_config(config_path: Path) -> EvaluationConfig:
    """Load evaluation configuration."""
    with config_path.open("r") as f:
        raw_config: dict[str, Any] = yaml.safe_load(f) or {}
    return EvaluationConfig.model_validate(raw_config)


def _resolve_config_path(config: str) -> Path:
    config_path = Path(config)
    if config_path.exists():
        return config_path
    return WORKDIR / "configs" / config


def _stage_results_artifact(run_output_dir: Path, results_artifact_dir: Path | None, run_id: str) -> None:
    if results_artifact_dir is None:
        return

    artifact_run_dir = results_artifact_dir / "transcription" / run_id
    for relative in sorted(RESULTS_RELATIVE_PATHS):
        src = run_output_dir / relative
        if not src.is_file():
            msg = f"Expected non-sensitive result file does not exist: {src}"
            raise FileNotFoundError(msg)
        dest = artifact_run_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def _load_dataset(
    loader_name: str,
    input_dir: Path | None,
    num_samples: int | None,
    sample_duration_fraction: float | None,
) -> DatasetProtocol:
    try:
        loader = DATASET_LOADER_REGISTRY[loader_name]
    except KeyError as exc:
        msg = f"Unknown dataset loader: {loader_name}"
        raise ValueError(msg) from exc
    return loader.load(
        input_dir=input_dir,
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
    )


def _run_blob_evaluation(config: EvaluationConfig, results_artifact_dir: Path | None) -> int:
    if config.blob.input_prefix is None:
        msg = "blob.input_prefix is required when blob.enabled is true"
        raise ValueError(msg)
    blob = EvalBlobStorage.from_account_urls(
        restricted_account_url=config.blob.restricted_account_url,
        shared_account_url=config.blob.shared_account_url,
    )

    with tempfile.TemporaryDirectory(prefix="evals-transcription-") as staging:
        staging_dir = Path(staging)
        input_dir = stage_dataset_prefix(blob, config.blob.input_prefix, staging_dir / "input")
        dataset_loader = config.dataset_loader or "audio_files"
        dataset = _load_dataset(
            dataset_loader,
            input_dir,
            config.num_samples,
            config.sample_duration_fraction,
        )
        outcome = _run_from_config(
            config,
            dataset=dataset,
            output_dir=staging_dir / "output",
            structured_output=True,
        )

        _stage_results_artifact(outcome.run_output_dir, results_artifact_dir, outcome.run_id)
        published = publish_run_outputs(
            blob,
            outcome.run_output_dir,
            outcome.run_id,
            output_prefix=config.blob.output_prefix,
            eval_type="transcription",
            results_relative_paths=RESULTS_RELATIVE_PATHS,
        )
        logger.info("Published outputs to blob storage: %s", published)
        return outcome.exit_code


def _run_from_config(
    config: EvaluationConfig,
    *,
    dataset: DatasetProtocol | None = None,
    output_dir: Path | None = None,
    structured_output: bool = False,
) -> EvaluationRunOutcome:
    return run_evaluation_with_outputs(
        num_samples=config.num_samples,
        sample_duration_fraction=config.sample_duration_fraction,
        prepare_only=config.prepare_only,
        max_workers=config.max_workers,
        adapter_names=config.adapters,
        check_drift_thresholds=config.check_drift_thresholds,
        dataset=dataset,
        output_dir=output_dir,
        structured_output=structured_output,
    )


def main() -> None:
    """Run the transcription eval CLI."""
    parser = argparse.ArgumentParser(description="Run transcription evaluation")
    parser.add_argument(
        "--config",
        type=str,
        default="smoketest.yaml",
        help="Path to config file (default: smoketest.yaml in configs/)",
    )
    parser.add_argument(
        "--results-artifact-dir",
        type=str,
        default=None,
        help="Directory for non-sensitive result files.",
    )
    args = parser.parse_args()

    config_path = _resolve_config_path(args.config)
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)

    config = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)

    results_artifact_dir = Path(args.results_artifact_dir) if args.results_artifact_dir is not None else None
    if config.blob.enabled:
        exit_code = _run_blob_evaluation(config, results_artifact_dir)
    else:
        exit_code = _run_from_config(config).exit_code
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

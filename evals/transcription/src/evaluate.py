from __future__ import annotations

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from common.audio.ffmpeg import get_duration
from common.settings import get_settings
from evals.transcription.src.adapters.base import ServiceTranscriptionAdapter
from evals.transcription.src.adapters.registry import ADAPTER_REGISTRY
from evals.transcription.src.config_validation import get_config
from evals.transcription.src.core.dataset import (
    DEFAULT_DATASET_NAME,
    load_benchmark_dataset,
    prepare_audio_for_transcription,
)
from evals.transcription.src.core.results import save_results
from evals.transcription.src.core.runner import run_engines_parallel
from evals.transcription.src.drift import apply_drift_thresholds

settings = get_settings()
WORKDIR = Path(__file__).resolve().parent.parent

logger = logging.getLogger(__name__)


def run_evaluation(
    num_samples: int | None = None,
    sample_duration_fraction: float | None = None,
    prepare_only: bool = False,
    max_workers: int | None = None,
    adapter_names: list[str] | None = None,
    check_drift_thresholds: bool = False,
    dataset_name: str = DEFAULT_DATASET_NAME,
    samples_per_group: int | None = None,
    input_dir: Path | None = None,
) -> int:
    """
    Runs transcription evaluation on the specified dataset with configured adapters.

    Returns a process exit code. 0 for success (and for drift review). 1 when drift fail or
    floor checks breach. Drift checks run only when check_drift_thresholds is true.

    dataset_name selects a source from DATASET_REGISTRY. input_dir overrides that
    dataset's Arrow and processed cache directory, defaulting to its own location under input/.
    samples_per_group is only supported by datasets with published groups.
    """
    output_dir = WORKDIR / "output"
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d_%H%M%S")
    run_id = f"eval_{timestamp}"
    output_path = output_dir / f"evaluation_results_{timestamp}.json"

    logger.info("Loading dataset...")
    dataset = load_benchmark_dataset(
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
        dataset_name=dataset_name,
        samples_per_group=samples_per_group,
        input_dir=input_dir,
    )

    indices = list(range(len(dataset)))
    if not indices:
        message = f"Dataset {dataset_name!r} produced no samples; check sampling options and cached metadata."
        raise ValueError(message)
    logger.info("Loaded %d samples from the dataset", len(indices))

    if prepare_only:
        logger.info("=== Dataset Preparation Complete ===")
        logger.info("Prepared %d meetings", len(indices))
        return 0

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

    save_results(results, output_path)

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
    logger.info("Results saved to: %s", output_path)

    if check_drift_thresholds:
        return apply_drift_thresholds(
            results,
            output_dir,
            timestamp,
            diarization_capabilities={
                adapter.name: dataset.supports_diarization and adapter.supports_diarization for adapter in adapters
            },
        )
    return 0


def load_config(config_path: Path) -> dict[str, object]:
    """
    Loads evaluation configuration from YAML file.
    """
    with config_path.open("r") as f:
        config: dict[str, object] = yaml.safe_load(f)
        return config


def main() -> None:
    """
    Parses command-line arguments and runs transcription evaluation.
    """
    parser = argparse.ArgumentParser(description="Run transcription evaluation")
    parser.add_argument(
        "--config",
        type=str,
        default="smoketest.yaml",
        help="Path to config file (default: smoketest.yaml in configs/)",
    )
    args = parser.parse_args()

    config_path = WORKDIR / "configs" / args.config
    if not config_path.exists():
        msg = f"Config file not found: {config_path}"
        raise FileNotFoundError(msg)

    config = load_config(config_path)
    logger.info("Loaded config from: %s", config_path)

    num_samples = get_config(config, "num_samples", int)
    max_workers = get_config(config, "max_workers", int)
    prepare_only = bool(get_config(config, "prepare_only", bool, default=False))
    check_drift_thresholds = bool(get_config(config, "check_drift_thresholds", bool, default=False))
    adapter_names = get_config(config, "adapters", list, required=True)
    dataset_name = get_config(config, "dataset", str) or DEFAULT_DATASET_NAME
    samples_per_group = get_config(config, "samples_per_group", int)
    input_dir_raw = get_config(config, "input_dir", str)
    input_dir = Path(input_dir_raw).expanduser() if input_dir_raw else None
    if input_dir is not None and not input_dir.is_absolute():
        input_dir = (config_path.parent / input_dir).resolve()

    sample_duration_fraction_raw = config.get("sample_duration_fraction")
    sample_duration_fraction: float | None = None
    if sample_duration_fraction_raw is not None:
        if not isinstance(sample_duration_fraction_raw, int | float):
            msg = (
                f"Config field 'sample_duration_fraction' must be a number, "
                f"got {type(sample_duration_fraction_raw).__name__}"
            )
            raise TypeError(msg)
        sample_duration_fraction = float(sample_duration_fraction_raw)

    exit_code = run_evaluation(
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
        prepare_only=prepare_only,
        max_workers=max_workers,
        adapter_names=adapter_names,
        check_drift_thresholds=check_drift_thresholds,
        dataset_name=dataset_name,
        samples_per_group=samples_per_group,
        input_dir=input_dir,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

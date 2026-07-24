"""Stage the dataset from blob and publish run outputs back, split results vs per-entry debug."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from evals.summarisation.src.common.config import AppConfig

if TYPE_CHECKING:
    from evals.summarisation.src.common.blob_storage import EvalBlobStorage

logger = logging.getLogger(__name__)

# summary.json is the only aggregated artefact; everything else is per-entry debug data.
RESULTS_FILENAMES = frozenset({"summary.json"})


def output_prefix_for(cfg: AppConfig, run_id: str, subtype: str | None = None) -> str:
    eval_type = subtype or cfg.run.eval_type
    base = cfg.blob.output_prefix.rstrip("/")
    return f"{base}/{eval_type}/{run_id}" if base else f"{eval_type}/{run_id}"


def stage_dataset(cfg: AppConfig, blob: EvalBlobStorage, dest_dir: Path) -> Path:
    if not cfg.dataset.blob_path:
        msg = "dataset.blob_path must be set when dataset.source is 'blob'"
        raise ValueError(msg)
    dest_path = dest_dir / Path(cfg.dataset.blob_path).name
    return blob.download_blob(cfg.blob.input_container, cfg.dataset.blob_path, dest_path)


def publish_run_outputs(
    cfg: AppConfig,
    blob: EvalBlobStorage,
    run_output_dir: Path,
    run_id: str,
    subtype: str | None = None,
) -> dict[str, str]:
    prefix = output_prefix_for(cfg, run_id, subtype)
    published: dict[str, str] = {}
    for path in sorted(p for p in run_output_dir.rglob("*") if p.is_file()):
        relative = path.relative_to(run_output_dir).as_posix()
        is_result = path.name in RESULTS_FILENAMES
        container = cfg.blob.results_container if is_result else cfg.blob.debug_container
        blob_name = f"{prefix}/{relative}"
        blob.upload_file(container, blob_name, path)
        published[relative] = f"{container}/{blob_name}"
    logger.info("Published %d output files for run %s", len(published), run_id)
    return published

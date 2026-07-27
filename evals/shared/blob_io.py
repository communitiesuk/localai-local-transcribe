"""Stage the dataset from blob and publish run outputs back, split results vs per-entry debug."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from evals.shared.blob_storage import DEBUG_CONTAINER, INPUT_CONTAINER, RESULTS_CONTAINER

if TYPE_CHECKING:
    from collections.abc import Iterable

    from evals.shared.blob_storage import EvalBlobStorage

logger = logging.getLogger(__name__)


def output_prefix_for(output_prefix: str, eval_type: str, run_id: str, subtype: str | None = None) -> str:
    eval_type = subtype or eval_type
    base = output_prefix.rstrip("/")
    return f"{base}/{eval_type}/{run_id}" if base else f"{eval_type}/{run_id}"


def stage_dataset(blob: EvalBlobStorage, blob_path: str | None, dest_dir: Path) -> Path:
    if not blob_path:
        msg = "dataset.blob_path must be set when dataset.source is 'blob'"
        raise ValueError(msg)
    dest_path = dest_dir / Path(blob_path).name
    return blob.download_blob(INPUT_CONTAINER, blob_path, dest_path)


def publish_run_outputs(
    blob: EvalBlobStorage,
    run_output_dir: Path,
    run_id: str,
    *,
    output_prefix: str,
    eval_type: str,
    results_relative_paths: Iterable[str],
    subtype: str | None = None,
) -> dict[str, str]:
    prefix = output_prefix_for(output_prefix, eval_type, run_id, subtype)
    results = frozenset(results_relative_paths)
    published: dict[str, str] = {}
    for path in sorted(p for p in run_output_dir.rglob("*") if p.is_file()):
        relative = path.relative_to(run_output_dir).as_posix()
        is_result = relative in results
        container = RESULTS_CONTAINER if is_result else DEBUG_CONTAINER
        blob_name = f"{prefix}/{relative}"
        blob.upload_file(container, blob_name, path)
        published[relative] = f"{container}/{blob_name}"
    logger.info("Published %d output files for run %s", len(published), run_id)
    return published

"""Publish silver transcript outputs to the evals debug container."""

import argparse
import logging
from pathlib import Path

from evals.shared.blob_io import publish_run_outputs
from evals.shared.blob_storage import EvalBlobStorage


def publish_silver_outputs(output_dir: Path, run_id: str) -> dict[str, str]:
    """Upload all generated files under a run-specific debug prefix."""
    if not output_dir.is_dir():
        msg = f"Output directory does not exist: {output_dir}"
        raise NotADirectoryError(msg)

    blob = EvalBlobStorage.from_account_urls(require_shared=False)
    return publish_run_outputs(
        blob,
        output_dir,
        run_id,
        output_prefix="",
        eval_type="silver-transcripts",
        results_relative_paths=(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish silver transcript outputs to the evals debug container.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    publish_silver_outputs(args.output_dir.expanduser().resolve(), args.run_id)


if __name__ == "__main__":
    main()

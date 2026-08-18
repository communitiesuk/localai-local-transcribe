from __future__ import annotations

import asyncio
import shutil
import sys
import tempfile
from pathlib import Path

import orjson
import typer

from evals.shared.blob_io import publish_run_outputs, stage_dataset
from evals.shared.blob_storage import EvalBlobStorage
from evals.summarisation.src.common import AppConfig, RunSummary, load_config, run_halted
from evals.summarisation.src.hallucination.types import HallucinationInput

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = WORKDIR / "configs" / "smoke-test.yaml"

# Only summary.json is a headline result; everything else the run writes is per-entry debug output.
RESULTS_RELATIVE_PATHS = frozenset({"summary.json"})

app = typer.Typer()

config_path_arg = typer.Option(DEFAULT_CONFIG, "--config", exists=True, dir_okay=False, readable=True)
results_artifact_dir_arg = typer.Option(
    None,
    "--results-artifact-dir",
    file_okay=False,
    dir_okay=True,
    writable=True,
    help="Directory for non-sensitive result files safe to publish as a short-retention pipeline artifact.",
)


def _resolve_io_dirs(cfg: AppConfig, mode: str) -> tuple[Path, Path]:
    """Return the (input, output) directories for an eval mode that reads scenarios from disk."""
    if cfg.run.input_dir is None:
        msg = f"input_dir must be specified in config under run.input_dir for {mode} evaluation"
        raise ValueError(msg)
    return Path(cfg.run.input_dir), Path(cfg.run.output_dir)


def _make_blob(cfg: AppConfig) -> EvalBlobStorage | None:
    if not cfg.blob.enabled:
        return None
    return EvalBlobStorage.from_account_urls(
        cfg.blob.account_url,
        restricted_account_url=cfg.blob.restricted_account_url,
        shared_account_url=cfg.blob.shared_account_url,
    )


def _staged_output_dir(blob: EvalBlobStorage | None, cfg: AppConfig, staging_dir: Path) -> Path:
    return staging_dir / "output" if blob is not None else Path(cfg.run.output_dir)


def _publish(
    blob: EvalBlobStorage | None,
    cfg: AppConfig,
    run_output_dir: Path,
    run_id: str,
    subtype: str | None = None,
) -> None:
    if blob is None:
        return
    published = publish_run_outputs(
        blob,
        run_output_dir,
        run_id,
        output_prefix=cfg.blob.output_prefix,
        eval_type=cfg.run.eval_type,
        results_relative_paths=RESULTS_RELATIVE_PATHS,
        subtype=subtype,
    )
    typer.echo("Published outputs to blob storage:")
    for name, dest in published.items():
        typer.echo(f"  {name} -> {dest}")


def _stage_results_artifact(
    run_output_dir: Path,
    results_artifact_dir: Path | None,
    run_id: str,
    eval_type: str,
    results_relative_paths: frozenset[str],
) -> None:
    """Copy only non-sensitive result files to the pipeline artifact staging directory."""
    if results_artifact_dir is None:
        return

    artifact_run_dir = results_artifact_dir / eval_type / run_id
    for relative in sorted(results_relative_paths):
        src = run_output_dir / relative
        if not src.is_file():
            msg = f"Expected non-sensitive result file does not exist: {src}"
            raise FileNotFoundError(msg)
        dest = artifact_run_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def _fail_pipeline_if_halted(summary_path: Path) -> None:
    """Fail the standard-eval pipeline when the run halted before completing.

    Called only after outputs are published, so the summary.json explaining the failure is
    preserved even though the CLI exits non-zero.
    """
    with summary_path.open("rb") as f:
        summary: RunSummary = orjson.loads(f.read())

    if run_halted(summary):
        typer.echo(
            "Eval halted before completion (see errors in summary.json); failing pipeline.",
            err=True,
        )
        raise typer.Exit(code=1)


def _fail_pipeline_if_threshold_failed(review_path: Path) -> None:
    with review_path.open("rb") as f:
        review = orjson.loads(f.read())

    if not review.get("overall_passed", False):
        typer.echo("Eval thresholds breached (see threshold_review.json).", err=True)
        raise typer.Exit(code=1)


def _fail_pipeline_if_citation_gate_failed(summary_path: Path) -> None:
    with summary_path.open("rb") as f:
        outcomes = orjson.loads(f.read())["citation_outcomes"]

    typer.echo(f"Citation outcomes: {outcomes}")
    if outcomes["fail"] > 0:
        typer.echo(
            f"Citation gate: {outcomes['fail']} summary/summaries failed the claim citation rate threshold.",
            err=True,
        )
        raise typer.Exit(code=1)


async def _drain_pending_tasks() -> None:
    """Await any background tasks the eval left running so they finish before the process exits."""
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def run_bias_eval(cfg: AppConfig) -> None:
    from evals.summarisation.src.bias import run_counterfactual_eval
    from evals.summarisation.src.bias.bias_types import BiasEvalResults
    from evals.summarisation.src.bias.thresholds import has_threshold_failures

    input_dir, output_dir = _resolve_io_dirs(cfg, "bias")

    run_id, results_path = await run_counterfactual_eval(cfg, input_dir, output_dir)

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")

    await _drain_pending_tasks()

    with results_path.open("rb") as f:
        results = BiasEvalResults.model_validate(orjson.loads(f.read()))

    if has_threshold_failures(results):
        typer.echo("Bias thresholds breached: at least one SPC or 4/5 check failed.", err=True)
        raise typer.Exit(code=1)


async def run_security_eval(cfg: AppConfig) -> None:
    from evals.summarisation.src.security import run_security_eval as _run_security_eval

    input_dir, output_dir = _resolve_io_dirs(cfg, "security")

    run_id, results_path = await _run_security_eval(cfg, input_dir, output_dir)

    run_output_dir = output_dir / run_id
    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Summary: {run_output_dir / 'summary.json'}")

    await _drain_pending_tasks()


def run_standard_eval(
    cfg: AppConfig,
    blob: EvalBlobStorage | None,
    staging_dir: Path,
    results_artifact_dir: Path | None,
) -> list[HallucinationInput]:
    from evals.summarisation.src.optimisation import run_eval

    dataset_path = None
    if blob is not None and cfg.dataset.source == "blob":
        dataset_path = stage_dataset(blob, cfg.dataset.blob_path, staging_dir / "input" / "standard")
    output_dir = _staged_output_dir(blob, cfg, staging_dir)

    run_id, results_path, summary_path, hallucination_inputs_path = run_eval(
        cfg,
        split=cfg.run.split,
        limit=cfg.run.limit,
        prompt_version=cfg.run.prompt_version,
        output_dir=output_dir,
        dataset_path=dataset_path,
    )

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Summary: {summary_path}")
    typer.echo(f"Hallucination inputs: {hallucination_inputs_path}")

    # Stage the non-sensitive result before blob upload. If upload fails, the pipeline can
    # still publish this short-retention artifact without exposing debug files.
    _stage_results_artifact(
        results_path.parent, results_artifact_dir, run_id, cfg.run.eval_type, RESULTS_RELATIVE_PATHS
    )

    # Publish before the failure decision so a halted run's artifacts (summary.json with the
    # error list that explains the halt) survive the staging temp-dir teardown.
    _publish(blob, cfg, results_path.parent, run_id)

    _fail_pipeline_if_halted(summary_path)
    _fail_pipeline_if_threshold_failed(results_path.parent / "threshold_review.json")

    with hallucination_inputs_path.open("rb") as f:
        return [HallucinationInput.model_validate(item) for item in orjson.loads(f.read())]


@app.callback(invoke_without_command=True)
def run(
    config: Path = config_path_arg,
    results_artifact_dir: Path | None = results_artifact_dir_arg,
) -> None:
    cfg = load_config(config)

    if cfg.dataset.source == "blob" and not cfg.blob.enabled:
        msg = "dataset.source: blob requires blob.enabled: true"
        raise ValueError(msg)

    if cfg.blob.enabled and cfg.run.eval_type != "standard":
        typer.echo(
            f"Warning: blob.enabled is set but eval_type is '{cfg.run.eval_type}'; blob storage is only "
            "used for standard evals, so outputs will stay on local disk.",
            err=True,
        )

    if cfg.hallucination.enabled and cfg.run.eval_type != "standard":
        msg = "Hallucination eval requires eval_type: standard"
        raise ValueError(msg)

    if cfg.run.eval_type == "bias":
        asyncio.run(run_bias_eval(cfg))
        return
    if cfg.run.eval_type == "security":
        asyncio.run(run_security_eval(cfg))
        return
    if cfg.run.eval_type != "standard":
        msg = f"Unknown eval_type: {cfg.run.eval_type}. Must be 'standard', 'bias' or 'security'"
        raise ValueError(msg)

    blob = _make_blob(cfg)

    # Only the standard eval (and its optional hallucination add-on) stages to a temp dir; scoping
    # its lifetime here keeps the C1 publish-before-teardown ordering clear.
    with tempfile.TemporaryDirectory(prefix="evals-summarisation-") as staging:
        staging_dir = Path(staging)

        hallucination_inputs = run_standard_eval(cfg, blob, staging_dir, results_artifact_dir)

        if cfg.hallucination.enabled:
            from evals.summarisation.src.hallucination import run_hallucination_eval
            from evals.summarisation.src.hallucination.constants import SUMMARY_FILENAME

            output_dir = _staged_output_dir(blob, cfg, staging_dir)
            h_run_id, h_results = run_hallucination_eval(
                cfg,
                inputs=hallucination_inputs,
                output_dir=output_dir,
            )
            typer.echo(f"\nHallucination run ID: {h_run_id}")
            typer.echo(f"Hallucination results: {h_results}")

            _publish(blob, cfg, h_results.parent, h_run_id, subtype="hallucination")
            _fail_pipeline_if_citation_gate_failed(h_results.parent / SUMMARY_FILENAME)


if __name__ == "__main__":
    sys.exit(app())

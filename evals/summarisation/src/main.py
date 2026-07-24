from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

import orjson
import typer

from evals.summarisation.src.common import AppConfig, load_config
from evals.summarisation.src.common.blob_io import publish_run_outputs, stage_dataset
from evals.summarisation.src.common.blob_storage import EvalBlobStorage
from evals.summarisation.src.hallucination.types import HallucinationInput

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = WORKDIR / "configs" / "smoke-test.yaml"

app = typer.Typer()

config_path_arg = typer.Option(DEFAULT_CONFIG, "--config", exists=True, dir_okay=False, readable=True)


def _resolve_io_dirs(cfg: AppConfig, mode: str) -> tuple[Path, Path]:
    """Return the (input, output) directories for an eval mode that reads scenarios from disk."""
    if cfg.run.input_dir is None:
        msg = f"input_dir must be specified in config under run.input_dir for {mode} evaluation"
        raise ValueError(msg)
    return Path(cfg.run.input_dir), Path(cfg.run.output_dir)


def _make_blob(cfg: AppConfig) -> EvalBlobStorage | None:
    return EvalBlobStorage.from_config(cfg.blob) if cfg.blob.enabled else None


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
    published = publish_run_outputs(cfg, blob, run_output_dir, run_id, subtype)
    typer.echo("Published outputs to blob storage:")
    for name, dest in published.items():
        typer.echo(f"  {name} -> {dest}")


async def _drain_pending_tasks() -> None:
    """Await any background tasks the eval left running so they finish before the process exits."""
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


async def run_bias_eval(config: Path) -> None:
    from evals.summarisation.src.bias import run_counterfactual_eval
    from evals.summarisation.src.bias.bias_types import BiasEvalResults
    from evals.summarisation.src.bias.thresholds import has_threshold_failures

    cfg = load_config(config)
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


async def run_security_eval(config: Path) -> None:
    from evals.summarisation.src.security import run_security_eval as _run_security_eval

    cfg = load_config(config)
    input_dir, output_dir = _resolve_io_dirs(cfg, "security")

    run_id, results_path = await _run_security_eval(cfg, input_dir, output_dir)

    run_output_dir = output_dir / run_id
    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Summary: {run_output_dir / 'summary.json'}")

    await _drain_pending_tasks()


def run_standard_eval(cfg: AppConfig, blob: EvalBlobStorage | None, staging_dir: Path) -> list[HallucinationInput]:
    from evals.summarisation.src.optimisation import run_eval

    dataset_path = None
    if blob is not None and cfg.dataset.source == "blob":
        dataset_path = stage_dataset(cfg, blob, staging_dir / "input" / "standard")
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

    with hallucination_inputs_path.open("rb") as f:
        hallucination_inputs = [HallucinationInput.model_validate(item) for item in orjson.loads(f.read())]

    _publish(blob, cfg, results_path.parent, run_id)

    return hallucination_inputs


@app.callback(invoke_without_command=True)
def run(
    config: Path = config_path_arg,
) -> None:
    cfg = load_config(config)

    blob = _make_blob(cfg) if cfg.run.eval_type == "standard" else None

    hallucination_inputs: list[HallucinationInput] = []

    with tempfile.TemporaryDirectory(prefix="evals-summarisation-") as staging:
        staging_dir = Path(staging)

        if cfg.run.eval_type == "bias":
            asyncio.run(run_bias_eval(config))
        elif cfg.run.eval_type == "security":
            asyncio.run(run_security_eval(config))
        elif cfg.run.eval_type == "standard":
            hallucination_inputs = run_standard_eval(cfg, blob, staging_dir)
        else:
            msg = f"Unknown eval_type: {cfg.run.eval_type}. Must be 'standard', 'bias' or 'security'"
            raise ValueError(msg)

        if cfg.hallucination.enabled:
            from evals.summarisation.src.hallucination import run_hallucination_eval

            if not hallucination_inputs:
                msg = "Hallucination eval requires eval_type: standard"
                raise ValueError(msg)

            output_dir = _staged_output_dir(blob, cfg, staging_dir)
            h_run_id, h_results = run_hallucination_eval(
                cfg,
                inputs=hallucination_inputs,
                output_dir=output_dir,
            )
            typer.echo(f"\nHallucination run ID: {h_run_id}")
            typer.echo(f"Hallucination results: {h_results}")

            _publish(blob, cfg, h_results.parent, h_run_id, subtype="hallucination")


if __name__ == "__main__":
    sys.exit(app())

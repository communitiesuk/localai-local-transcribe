from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import orjson
import typer

from evals.summarisation.src.common import load_config
from evals.summarisation.src.hallucination.types import HallucinationInput

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = WORKDIR / "configs" / "smoke-test.yaml"

app = typer.Typer()

config_path_arg = typer.Option(DEFAULT_CONFIG, "--config", exists=True, dir_okay=False, readable=True)


async def run_bias_eval(config: Path) -> None:
    from evals.summarisation.src.bias import run_counterfactual_eval
    from evals.summarisation.src.bias.bias_types import BiasEvalResults
    from evals.summarisation.src.bias.thresholds import has_threshold_failures

    cfg = load_config(config)

    if cfg.run.input_dir is None:
        msg = "input_dir must be specified in config under run.input_dir for bias evaluation"
        raise ValueError(msg)

    input_dir = Path(cfg.run.input_dir)
    output_dir = Path(cfg.run.output_dir)

    run_id, results_path = await run_counterfactual_eval(cfg, input_dir, output_dir)

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    with results_path.open("rb") as f:
        results = BiasEvalResults.model_validate(orjson.loads(f.read()))

    if has_threshold_failures(results):
        typer.echo("Bias thresholds breached: at least one SPC or 4/5 check failed.", err=True)
        raise typer.Exit(code=1)


async def run_security_eval(config: Path) -> None:
    from evals.summarisation.src.security import run_security_eval as _run_security_eval

    cfg = load_config(config)

    if cfg.run.input_dir is None:
        msg = "input_dir must be specified in config under run.input_dir for security evaluation"
        raise ValueError(msg)

    input_dir = Path(cfg.run.input_dir)
    output_dir = Path(cfg.run.output_dir)

    run_id, results_path = await _run_security_eval(cfg, input_dir, output_dir)

    run_output_dir = output_dir / run_id
    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Report: {run_output_dir / 'report.md'}")
    typer.echo(f"Conclusions: {run_output_dir / 'CONCLUSIONS.md'}")

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def run_standard_eval(config: Path) -> list[HallucinationInput]:
    from evals.summarisation.src.optimisation import run_eval

    cfg = load_config(config)
    run_id, results_path, summary_path, hallucination_inputs_path = run_eval(
        cfg,
        split=cfg.run.split,
        limit=cfg.run.limit,
        prompt_version=cfg.run.prompt_version,
    )

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Summary: {summary_path}")
    typer.echo(f"Hallucination inputs: {hallucination_inputs_path}")

    with hallucination_inputs_path.open("rb") as f:
        return [HallucinationInput.model_validate(item) for item in orjson.loads(f.read())]


@app.callback(invoke_without_command=True)
def run(
    config: Path = config_path_arg,
) -> None:
    cfg = load_config(config)

    hallucination_inputs: list[HallucinationInput] = []

    if cfg.run.eval_type == "bias":
        asyncio.run(run_bias_eval(config))
    elif cfg.run.eval_type == "security":
        asyncio.run(run_security_eval(config))
    elif cfg.run.eval_type == "standard":
        hallucination_inputs = run_standard_eval(config)
    else:
        msg = f"Unknown eval_type: {cfg.run.eval_type}. Must be 'standard', 'bias' or 'security'"
        raise ValueError(msg)

    if cfg.hallucination.enabled:
        from evals.summarisation.src.hallucination import run_hallucination_eval

        if not hallucination_inputs:
            msg = "Hallucination eval requires eval_type: standard"
            raise ValueError(msg)

        h_run_id, h_results = run_hallucination_eval(
            cfg,
            inputs=hallucination_inputs,
            output_dir=Path(cfg.run.output_dir),
        )
        typer.echo(f"\nHallucination run ID: {h_run_id}")
        typer.echo(f"Hallucination results: {h_results}")


if __name__ == "__main__":
    sys.exit(app())

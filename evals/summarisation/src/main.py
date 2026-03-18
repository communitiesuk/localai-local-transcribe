from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import orjson
import typer

from evals.summarisation.src.bias.types import PlottingOutput
from evals.summarisation.src.bias.visualization.reporter import generate_visualizations
from evals.summarisation.src.common import load_config

WORKDIR = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = WORKDIR / "configs" / "smoke-test.yaml"

app = typer.Typer()

config_path_arg = typer.Option(DEFAULT_CONFIG, "--config", exists=True, dir_okay=False, readable=True)


async def run_bias_eval(config: Path) -> None:
    from evals.summarisation.src.bias import run_counterfactual_eval

    cfg = load_config(config)

    if cfg.run.input_dir is None:
        msg = "input_dir must be specified in config under run.input_dir for bias evaluation"
        raise ValueError(msg)

    input_dir = Path(cfg.run.input_dir)
    output_dir = Path(cfg.run.output_dir)

    run_id, results_path = await run_counterfactual_eval(cfg, input_dir, output_dir)

    with results_path.open("rb") as f:
        plotting_output = PlottingOutput.model_validate(orjson.loads(f.read()))

    run_output_dir = output_dir / run_id
    generate_visualizations(plotting_output.comparisons, run_output_dir)

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Visualizations: {run_output_dir / 'visualizations'}")

    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def run_standard_eval(config: Path) -> None:
    from evals.summarisation.src.optimisation import run_eval

    cfg = load_config(config)
    run_id, results_path, summary_path = run_eval(
        cfg,
        split=cfg.run.split,
        limit=cfg.run.limit,
        prompt_version=cfg.run.prompt_version,
    )

    typer.echo(f"\nRun ID: {run_id}")
    typer.echo(f"Results: {results_path}")
    typer.echo(f"Summary: {summary_path}")


@app.callback(invoke_without_command=True)
def run(
    config: Path = config_path_arg,
) -> None:
    cfg = load_config(config)

    if cfg.run.eval_type == "bias":
        asyncio.run(run_bias_eval(config))
    elif cfg.run.eval_type == "standard":
        run_standard_eval(config)
    else:
        msg = f"Unknown eval_type: {cfg.run.eval_type}. Must be 'standard' or 'bias'"
        raise ValueError(msg)


if __name__ == "__main__":
    sys.exit(app())

from __future__ import annotations

import logging
import uuid
from pathlib import Path

import orjson

from evals.summarisation.src.bias.bias_types import CounterfactualEvalRecord, IterationMetrics
from evals.summarisation.src.bias.constants import RESULTS_FILENAME, SUMMARY_FILENAME
from evals.summarisation.src.bias.data.loader import discover_counterfactual_files
from evals.summarisation.src.bias.data.record_builder import process_counterfactual_file
from evals.summarisation.src.bias.output_formatter import build_results, create_summary
from evals.summarisation.src.bias.regard_scorer import REGARDScorer
from evals.summarisation.src.bias.sentiment_analyzer import SentimentAnalyzer
from evals.summarisation.src.bias.spc import build_spc_baseline, load_spc_baseline, save_spc_baseline
from evals.summarisation.src.bias.thresholds import apply_thresholds
from evals.summarisation.src.common import AppConfig, build_metrics

logger = logging.getLogger(__name__)


async def run_counterfactual_eval(
    cfg: AppConfig,
    input_dir: Path,
    output_dir: Path,
) -> tuple[str, Path]:
    """
    Runs counterfactual bias evaluation on dataset and generates results and summary.
    """
    # In emit mode we derive the baseline from this run, so there is nothing to load; otherwise
    # validate the required baseline up front (fail fast before models load or dirs are created).
    emit_spc_baseline = cfg.run.emit_spc_baseline
    spc_baseline = None if emit_spc_baseline else load_spc_baseline(input_dir)

    if cfg.run.num_iterations is None:
        msg = "num_iterations must be specified in config for bias evaluations"
        raise ValueError(msg)

    num_iterations: int = cfg.run.num_iterations
    if num_iterations <= 0:
        msg = f"num_iterations must be positive, got {num_iterations}"
        raise ValueError(msg)

    run_id = str(uuid.uuid4())
    run_output_dir = output_dir / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    results_path = run_output_dir / RESULTS_FILENAME
    summary_path = run_output_dir / SUMMARY_FILENAME

    metrics = build_metrics(cfg)
    sentiment_analyzer = SentimentAnalyzer()
    regard_scorer = REGARDScorer()

    counterfactual_files = discover_counterfactual_files(input_dir)
    logger.info("Found %d counterfactual files to process", len(counterfactual_files))
    logger.info("Running %d iterations per transcript", num_iterations)

    all_records: list[CounterfactualEvalRecord] = []
    baseline_cache: dict[str, tuple[list[str], list[IterationMetrics], int, int]] = {}

    template_name = cfg.prompts.summarizer_template_name

    for file_path in counterfactual_files:
        record = await process_counterfactual_file(
            file_path,
            run_id,
            num_iterations,
            metrics,
            sentiment_analyzer,
            regard_scorer,
            cfg,
            baseline_cache,
            template_name,
        )
        all_records.append(record)

    results = build_results(all_records, run_id, cfg, num_iterations)
    if spc_baseline is None:
        baseline = build_spc_baseline(results.comparisons, description=f"Generated from run {run_id}")
        save_spc_baseline(baseline, run_output_dir)
    else:
        apply_thresholds(results, all_records, spc_baseline)
    try:
        with results_path.open("wb") as f:
            f.write(orjson.dumps(results.model_dump(), option=orjson.OPT_INDENT_2))
    except OSError as e:
        msg = f"Failed to write results to {results_path}: {e}"
        logger.error(msg)
        raise RuntimeError(msg) from e

    summary_data = create_summary(all_records, run_id, cfg)
    try:
        with summary_path.open("wb") as f:
            f.write(orjson.dumps(summary_data.model_dump(), option=orjson.OPT_INDENT_2))
    except OSError as e:
        msg = f"Failed to write summary to {summary_path}: {e}"
        logger.error(msg)
        raise RuntimeError(msg) from e

    logger.info("Evaluation complete. Results written to %s", run_output_dir)
    return run_id, results_path

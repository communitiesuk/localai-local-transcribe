from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

import orjson

from evals.summarisation.src.common.config import AppConfig
from evals.summarisation.src.common.jsonl import write_jsonl
from evals.summarisation.src.constants import citation_rate_outcome
from evals.summarisation.src.hallucination.constants import RESULTS_FILENAME, SUMMARY_FILENAME
from evals.summarisation.src.hallucination.extractor import build_statements
from evals.summarisation.src.hallucination.types import HallucinationInput, HallucinationReport

logger = logging.getLogger(__name__)


def run_hallucination_eval(
    cfg: AppConfig,
    inputs: list[HallucinationInput],
    output_dir: Path,
) -> tuple[str, Path]:
    """Runs the hallucination evaluation pipeline.

    Uncited claims are sourced directly from the generation step (via
    common.templates.citations.add_citations_to_minute), so no additional
    LLM calls are made here.

    Writes one JSONL results file and one JSON summary file.
    Returns (run_id, results_path).
    """
    run_id = str(uuid.uuid4())
    run_output_dir = output_dir / run_id
    run_output_dir.mkdir(parents=True, exist_ok=True)

    results_path = run_output_dir / RESULTS_FILENAME
    summary_path = run_output_dir / SUMMARY_FILENAME

    logger.info("Running hallucination eval on %d inputs", len(inputs))

    reports: list[HallucinationReport] = []

    for record in inputs:
        logger.info("Processing example_id=%s", record.example_id)
        try:
            statements = build_statements(record.uncited_claims)
            n_hallucinations = len(statements)
            n_supported = max(0, record.total_claims - n_hallucinations)
            total = record.total_claims
            hallucination_rate = round(n_hallucinations / total, 3) if total > 0 else 0.0
            outcome = citation_rate_outcome(n_supported, total)

            report = HallucinationReport(
                run_id=run_id,
                example_id=record.example_id,
                hypothesis_model=record.hypothesis_model,
                template_name=cfg.prompts.summarizer_template_name,
                timestamp=datetime.now(UTC),
                prompt_version=cfg.run.prompt_version,
                statements=statements,
                metrics={
                    "n_hallucinations": n_hallucinations,
                    "n_supported": n_supported,
                    "hallucination_rate": hallucination_rate,
                    "no_hallucinations": n_hallucinations == 0,
                    "citation_outcome": outcome,
                },
            )
            reports.append(report)
        except Exception:
            logger.exception("Failed to process example_id=%s", record.example_id)

    write_jsonl(results_path, [r.model_dump(mode="json") for r in reports])

    n_examples = len(inputs)
    processed = len(reports)
    total_hallucinated = sum(int(r.metrics["n_hallucinations"]) for r in reports)
    total_supported = sum(int(r.metrics["n_supported"]) for r in reports)
    grand_total = total_hallucinated + total_supported
    overall_hallucination_rate = round(total_hallucinated / grand_total, 3) if grand_total > 0 else 0.0

    summary: dict[str, str | int | float | None | dict[str, float]] = {
        "run_id": run_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "template_name": cfg.prompts.summarizer_template_name,
        "dataset_version": cfg.run.dataset_version,
        "engine_version": inputs[0].hypothesis_model if inputs else None,
        "prompt_version": cfg.run.prompt_version,
        "n_examples": n_examples,
        "processed": processed,
        "metrics": {
            "hallucination_rate": overall_hallucination_rate,
            "total_hallucinated_claims": total_hallucinated,
            "total_supported_claims": total_supported,
        },
    }

    summary_path.write_bytes(orjson.dumps(summary, option=orjson.OPT_INDENT_2))
    logger.info("Hallucination eval complete. Results: %s", run_output_dir)

    return run_id, results_path

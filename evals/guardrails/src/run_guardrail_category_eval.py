from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from tenacity import RetryError

from common.services.minute_handler_service import MinuteHandlerService
from common.settings import get_settings
from common.types import DialogueEntry, FailureCategory, FailureMode, GuardrailScore

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CONFIG_PATH = Path("evals/guardrails/configs/default.json")
DEFAULT_CASES_PATH = Path("evals/guardrails/input/cases.json")
DEFAULT_OUTPUT_PATH = Path("evals/guardrails/output/results.json")


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        msg = f"Expected JSON object in {path}"
        raise ValueError(msg)
    return data


def _read_cases(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        msg = f"Expected JSON list in {path}"
        raise ValueError(msg)
    return data


def _read_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _read_json(path)


def _repo_path(path: Path | str) -> Path:
    resolved = Path(path)
    if resolved.is_absolute():
        return resolved
    return REPO_ROOT / resolved


def _summary_from_output(path: Path) -> str:
    data = _read_json(path)
    try:
        summary = data["record"]["candidate"]["summary"]
    except KeyError as exc:
        msg = f"Could not find record.candidate.summary in {path}"
        raise ValueError(msg) from exc
    if not isinstance(summary, str):
        msg = f"Summary is not a string in {path}"
        raise ValueError(msg)
    return summary


def _transcript_from_output(path: Path) -> list[DialogueEntry]:
    data = _read_json(path)
    entries = data.get("dialogue_entries")
    if not isinstance(entries, list):
        msg = f"Could not find dialogue_entries list in {path}"
        raise ValueError(msg)
    return entries


def _normalise_category(category: str) -> str:
    try:
        return FailureCategory[category].name
    except KeyError:
        return FailureCategory(category).name


def _normalise_mode(mode: str) -> str:
    try:
        return FailureMode[mode].name
    except KeyError:
        return FailureMode(mode).name


def _normalise_expected(case: dict[str, Any], key: str) -> list[str]:
    values = case.get(key, [])
    if not isinstance(values, list):
        msg = f"{case['id']} has non-list {key}"
        raise ValueError(msg)
    if key == "expected_categories":
        return [_normalise_category(value) for value in values]
    return [_normalise_mode(value) for value in values]


def _apply_mutations(summary: str, mutations: list[dict[str, Any]]) -> str:
    mutated = summary
    for mutation in mutations:
        mutation_type = mutation["type"]
        if mutation_type == "append":
            mutated += mutation["text"]
        elif mutation_type == "replace":
            old = mutation["old"]
            count = int(mutation.get("count", -1))
            if old not in mutated:
                msg = f"Replacement text not found: {old}"
                raise ValueError(msg)
            mutated = mutated.replace(old, mutation["new"], count)
        elif mutation_type == "remove_lines_containing":
            needle = mutation["text"]
            mutated = "\n".join(line for line in mutated.splitlines() if needle not in line)
        elif mutation_type == "remove_between":
            start = mutated.find(mutation["start"])
            end = mutated.find(mutation["end"], start)
            if start == -1 or end == -1:
                msg = f"Section bounds not found: {mutation['start']} -> {mutation['end']}"
                raise ValueError(msg)
            mutated = mutated[:start] + mutated[end:]
        else:
            msg = f"Unsupported mutation type: {mutation_type}"
            raise ValueError(msg)
    return mutated


def _prediction_categories(score: GuardrailScore) -> list[str]:
    return sorted({detail.category.name for detail in score.categories})


def _prediction_modes(score: GuardrailScore) -> list[str]:
    return sorted({detail.mode.name for detail in score.categories})


def _f1(tp: int, fp: int, fn: int) -> float:
    denominator = (2 * tp) + fp + fn
    if denominator == 0:
        return 0.0
    return (2 * tp) / denominator


def _score_labels(results: list[dict[str, Any]], label_key: str, prediction_key: str) -> dict[str, Any]:
    labels = sorted(
        {label for result in results for label in [*result.get(label_key, []), *result.get(prediction_key, [])]}
    )
    per_label: dict[str, dict[str, float | int]] = {}
    total_tp = total_fp = total_fn = 0

    for label in labels:
        tp = fp = fn = 0
        for result in results:
            expected = set(result.get(label_key, []))
            predicted = set(result.get(prediction_key, []))
            if label in expected and label in predicted:
                tp += 1
            elif label not in expected and label in predicted:
                fp += 1
            elif label in expected and label not in predicted:
                fn += 1
        total_tp += tp
        total_fp += fp
        total_fn += fn
        per_label[label] = {"tp": tp, "fp": fp, "fn": fn, "f1": _f1(tp, fp, fn)}

    macro_values = [label_scores["f1"] for label_scores in per_label.values()]
    macro_f1 = sum(macro_values) / len(macro_values) if macro_values else 0.0
    return {
        "micro": {"tp": total_tp, "fp": total_fp, "fn": total_fn, "f1": _f1(total_tp, total_fp, total_fn)},
        "macro_f1": macro_f1,
        "per_label": per_label,
    }


def _score_binary(results: list[dict[str, Any]]) -> dict[str, float | int]:
    threshold = get_settings().GUARDRAIL_THRESHOLD
    tp = fp = tn = fn = 0
    for result in results:
        expected_flagged = bool(result["expected_categories"])
        predicted_flagged = bool(result["predicted_categories"]) or result["score"] < threshold
        if expected_flagged and predicted_flagged:
            tp += 1
        elif not expected_flagged and predicted_flagged:
            fp += 1
        elif not expected_flagged and not predicted_flagged:
            tn += 1
        else:
            fn += 1
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "f1": _f1(tp, fp, fn)}


def _error_message(exc: Exception) -> str:
    if isinstance(exc, RetryError):
        retry_exc = exc.last_attempt.exception()
        if retry_exc is not None:
            return f"{type(retry_exc).__name__}: {retry_exc}"
    return f"{type(exc).__name__}: {exc}"


async def _run_case(case: dict[str, Any], semaphore: asyncio.Semaphore) -> dict[str, Any]:
    summary_path = REPO_ROOT / case["summary_path"]
    transcript_path = REPO_ROOT / case["transcript_path"]
    mutations = case.get("mutations", [])
    if not isinstance(mutations, list):
        msg = f"{case['id']} has non-list mutations"
        raise ValueError(msg)

    summary = _apply_mutations(_summary_from_output(summary_path), mutations)
    transcript = _transcript_from_output(transcript_path)
    expected_categories = _normalise_expected(case, "expected_categories")
    expected_modes = _normalise_expected(case, "expected_modes")

    async with semaphore:
        try:
            score = await MinuteHandlerService.calculate_accuracy_score(summary, transcript)
        except Exception as exc:  # noqa: BLE001
            return {
                "id": case["id"],
                "description": case.get("description"),
                "error": _error_message(exc),
                "expected_categories": expected_categories,
                "expected_modes": expected_modes,
                "predicted_categories": [],
                "predicted_modes": [],
                "score": None,
                "reasoning": None,
                "category_exact_match": False,
                "mode_exact_match": False,
            }

    predicted_categories = _prediction_categories(score)
    predicted_modes = _prediction_modes(score)
    return {
        "id": case["id"],
        "description": case.get("description"),
        "expected_categories": expected_categories,
        "expected_modes": expected_modes,
        "predicted_categories": predicted_categories,
        "predicted_modes": predicted_modes,
        "score": score.score,
        "reasoning": score.reasoning,
        "category_details": [detail.model_dump(mode="json") for detail in score.categories],
        "category_exact_match": set(predicted_categories) == set(expected_categories),
        "mode_exact_match": set(predicted_modes) == set(expected_modes),
    }


async def _run(cases_path: Path, output_path: Path, concurrency: int, limit: int | None) -> dict[str, Any]:
    cases = [] if limit == 0 else _read_cases(cases_path)
    if limit is not None and limit > 0:
        cases = cases[:limit]
    semaphore = asyncio.Semaphore(concurrency)
    results = await asyncio.gather(*[_run_case(case, semaphore) for case in cases])
    completed_results = [result for result in results if result["score"] is not None]
    report = {
        "case_count": len(results),
        "completed_case_count": len(completed_results),
        "binary": _score_binary(completed_results),
        "categories": _score_labels(completed_results, "expected_categories", "predicted_categories"),
        "modes": _score_labels(completed_results, "expected_modes", "predicted_modes"),
        "results": results,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the minimal guardrail category eval.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--cases", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = _read_config(_repo_path(args.config))
    cases_path = args.cases or Path(config.get("cases_path", DEFAULT_CASES_PATH))
    output_path = args.output or Path(config.get("output_path", DEFAULT_OUTPUT_PATH))
    concurrency = args.concurrency or int(config.get("concurrency", 3))
    report = asyncio.run(_run(_repo_path(cases_path), _repo_path(output_path), concurrency, args.limit))
    sys.stdout.write(
        json.dumps(
            {
                "case_count": report["case_count"],
                "completed_case_count": report["completed_case_count"],
                "binary_f1": report["binary"]["f1"],
                "category_micro_f1": report["categories"]["micro"]["f1"],
                "category_macro_f1": report["categories"]["macro_f1"],
                "mode_micro_f1": report["modes"]["micro"]["f1"],
                "output": str(output_path),
            },
            indent=2,
        )
    )
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()

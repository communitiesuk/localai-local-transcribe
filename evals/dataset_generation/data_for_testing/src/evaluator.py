from typing import Any


def extract_spans(characteristics_output: dict) -> list[dict[str, Any]]:
    return [
        span
        for item in characteristics_output.get("detected_characteristics", [])
        for span in item.get("evidence_spans", [])
        if span.get("start_index") is not None and span.get("end_index") is not None
    ]


def evaluate_by_index(reference: dict, hypothesis: dict) -> dict[str, Any]:
    """Compares reference and hypothesis characteristics by span index containment.

    A reference span is a hit (TP) only when a hypothesis span fully contains it
    (hyp_start <= ref_start and hyp_end >= ref_end). Partial coverage is a miss (FN).
    Hypothesis spans that fully contain no reference span are false positives (FP).
    Oversized matches are hits but accrue undesirable_padding (excess character count).
    """
    ref_spans = extract_spans(reference)
    hyp_spans = extract_spans(hypothesis)

    annotation_results: list[dict[str, Any]] = []
    used_hyp_indices: set[int] = set()

    for ref in ref_spans:
        ann_start, ann_end = ref["start_index"], ref["end_index"]
        best: tuple[int, dict[str, Any], int] | None = None  # (padding, hyp, idx)

        for i, hyp in enumerate(hyp_spans):
            hyp_start, hyp_end = hyp["start_index"], hyp["end_index"]
            if hyp_start <= ann_start and hyp_end >= ann_end:
                pad = (ann_start - hyp_start) + (hyp_end - ann_end)
                if best is None or pad < best[0]:
                    best = (pad, hyp, i)

        if best is not None:
            padding, covering_hyp, hyp_idx = best
            used_hyp_indices.add(hyp_idx)
            annotation_results.append(
                {
                    "reference_span": ref,
                    "covering_hypothesis": covering_hyp,
                    "label": "TP",
                    "undesirable_padding": padding,
                }
            )
        else:
            annotation_results.append(
                {
                    "reference_span": ref,
                    "covering_hypothesis": None,
                    "label": "FN",
                    "undesirable_padding": 0,
                }
            )

    hypothesis_results: list[dict[str, Any]] = [
        {"hypothesis_span": hyp, "label": "TP" if i in used_hyp_indices else "FP"} for i, hyp in enumerate(hyp_spans)
    ]

    true_positive = sum(1 for r in annotation_results if r["label"] == "TP")
    false_negative = sum(1 for r in annotation_results if r["label"] == "FN")
    false_positive = sum(1 for r in hypothesis_results if r["label"] == "FP")

    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) > 0 else 0.0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    padded_hits = [r for r in annotation_results if r["label"] == "TP" and r["undesirable_padding"] > 0]
    total_excess = sum(r["undesirable_padding"] for r in annotation_results)

    metrics: dict[str, Any] = {
        "true_positive": true_positive,
        "false_negative": false_negative,
        "false_positive": false_positive,
        "precision": precision,
        "recall": recall,
        "f1_score": f1,
        "undesirable_padding": {
            "total_excess_chars": total_excess,
            "hits_with_padding": len(padded_hits),
            "hits_without_padding": true_positive - len(padded_hits),
            "average_excess_chars_per_padded_hit": total_excess / len(padded_hits) if padded_hits else 0.0,
        },
    }

    return {
        "annotation_results": annotation_results,
        "hypothesis_results": hypothesis_results,
        "summary": metrics,
    }

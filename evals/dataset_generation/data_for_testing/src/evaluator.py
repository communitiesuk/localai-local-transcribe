from typing import Any


def extract_spans(characteristics_output: dict) -> list[dict[str, Any]]:
    return [
        span
        for item in characteristics_output.get("detected_characteristics", [])
        for span in item.get("evidence_spans", [])
        if span.get("start_index") is not None and span.get("end_index") is not None
    ]


def _extract_spans_with_characteristic(characteristics_output: dict) -> list[tuple[dict[str, Any], str]]:
    """Return (span, characteristic) pairs for all valid spans.

    Used internally to enable characteristic-aware matching: a hypothesis span
    for 'Sex' should preferentially cover a reference span for 'Sex' rather than
    being shared with a 'Religion' reference span at the same position.
    """
    return [
        (span, item.get("characteristic", ""))
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

    **Characteristic-aware matching**: when multiple hypothesis spans at the same position
    exist (e.g. one for Race, one for Sex, one for Religion), each reference span is matched
    to the best **unused same-characteristic** span first.  Only if no same-characteristic
    span is available does it fall back to any covering span.  This ensures that the
    per-characteristic architecture (9 focused agents, each returning spans for a single
    characteristic) is evaluated correctly rather than penalising extra spans at the
    same position as false positives.
    """
    ref_spans = extract_spans(reference)
    hyp_spans = extract_spans(hypothesis)
    ref_chars = [char for _, char in _extract_spans_with_characteristic(reference)]
    hyp_chars = [char for _, char in _extract_spans_with_characteristic(hypothesis)]

    annotation_results: list[dict[str, Any]] = []
    used_hyp_indices: set[int] = set()

    for ref, ref_char in zip(ref_spans, ref_chars, strict=False):
        ann_start, ann_end = ref["start_index"], ref["end_index"]

        # Priority: prefer (unused + same-char) > (unused + any-char) > (used + same-char) > (used + any-char)
        best_priority: int | None = None
        best_padding = 0
        best_hyp: dict[str, Any] | None = None
        best_idx = -1

        for i, (hyp, hyp_char) in enumerate(zip(hyp_spans, hyp_chars, strict=False)):
            hyp_start, hyp_end = hyp["start_index"], hyp["end_index"]
            if hyp_start <= ann_start and hyp_end >= ann_end:
                pad = (ann_start - hyp_start) + (hyp_end - ann_end)
                already_used = i in used_hyp_indices
                same_char = hyp_char == ref_char
                # Lower priority value = better match
                priority = (2 if already_used else 0) + (0 if same_char else 1)
                if (
                    best_priority is None
                    or priority < best_priority
                    or (priority == best_priority and pad < best_padding)
                ):
                    best_priority, best_padding, best_hyp, best_idx = priority, pad, hyp, i

        if best_hyp is not None:
            used_hyp_indices.add(best_idx)
            annotation_results.append(
                {
                    "reference_span": ref,
                    "covering_hypothesis": best_hyp,
                    "label": "TP",
                    "undesirable_padding": best_padding,
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

    hypothesis_results = [
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

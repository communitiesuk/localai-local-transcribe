from evals.dataset_generation.data_for_testing.src.evaluate import evaluate_by_index


def make_span(start, end):
    return {"detected_characteristics": [{"evidence_spans": [{"start_index": start, "end_index": end}]}]}


def make_empty():
    return {"detected_characteristics": []}


def test_empty_inputs():
    """Tests the case where both reference and hypothesis have no detected characteristics."""
    reference = make_empty()
    hypothesis = make_empty()

    result = evaluate_by_index(reference, hypothesis)

    assert result["annotation_results"] == []
    assert result["hypothesis_results"] == []

    summary = result["summary"]
    assert summary["true_positive"] == 0
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 0
    assert summary["precision"] == 0.0
    assert summary["recall"] == 0.0
    assert summary["f1_score"] == 0.0
    assert summary["undesirable_padding"]["total_excess_chars"] == 0


def test_perfect_span_match():
    """Tests the case where the hypothesis perfectly matches the reference span."""
    reference = make_span(10, 20)
    hypothesis = make_span(10, 20)

    result = evaluate_by_index(reference, hypothesis)

    summary = result["summary"]

    assert summary["true_positive"] == 1
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 0
    assert summary["precision"] == 1.0
    assert summary["recall"] == 1.0
    assert summary["f1_score"] == 1.0

    padding = summary["undesirable_padding"]
    assert padding["total_excess_chars"] == 0
    assert padding["hits_with_padding"] == 0
    assert padding["hits_without_padding"] == 1

    ann = result["annotation_results"][0]
    assert ann["label"] == "TP"
    assert ann["undesirable_padding"] == 0


def test_oversized_hypothesis():
    """Tests the case where the hypothesis span is larger than the reference span, containing it."""
    reference = make_span(10, 20)
    hypothesis = make_span(5, 25)

    result = evaluate_by_index(reference, hypothesis)

    summary = result["summary"]

    assert summary["true_positive"] == 1
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 0

    padding = summary["undesirable_padding"]
    assert padding["total_excess_chars"] == 10
    assert padding["hits_with_padding"] == 1
    assert padding["hits_without_padding"] == 0
    assert padding["average_excess_chars_per_padded_hit"] == 10.0

    ann = result["annotation_results"][0]
    assert ann["label"] == "TP"
    assert ann["undesirable_padding"] == 10


def test_partial_overlap_counts_as_fn_and_fp():
    """Tests the case where the hypothesis partially overlaps with the reference but does not fully contain it."""
    reference = make_span(10, 20)
    hypothesis = make_span(15, 25)

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 0
    assert summary["false_negative"] == 1
    assert summary["false_positive"] == 1

    ann = result["annotation_results"][0]
    assert ann["label"] == "FN"

    hyp = result["hypothesis_results"][0]
    assert hyp["label"] == "FP"

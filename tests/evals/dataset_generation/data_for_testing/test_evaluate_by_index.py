from evals.dataset_generation.data_for_testing.src.evaluate import evaluate_by_index
from evals.dataset_generation.data_for_testing.src.evaluator import extract_spans


def make_span(start, end):
    return {"detected_characteristics": [{"evidence_spans": [{"start_index": start, "end_index": end}]}]}


def make_multi_span(*spans):
    return {"detected_characteristics": [{"evidence_spans": [{"start_index": s, "end_index": e} for s, e in spans]}]}


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


def test_reference_with_no_hypothesis():
    """Reference spans become FN when hypothesis has no spans."""
    reference = make_span(10, 20)
    hypothesis = make_empty()

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 0
    assert summary["false_negative"] == 1
    assert summary["false_positive"] == 0
    assert summary["precision"] == 0.0
    assert summary["recall"] == 0.0
    assert result["annotation_results"][0]["label"] == "FN"


def test_hypothesis_with_no_reference():
    """Hypothesis spans become FP when reference has no spans."""
    reference = make_empty()
    hypothesis = make_span(10, 20)

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 0
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 1
    assert summary["precision"] == 0.0
    assert result["hypothesis_results"][0]["label"] == "FP"


def test_multiple_spans_all_tp():
    """Multiple reference spans all matched exactly give perfect scores."""
    reference = make_multi_span((0, 10), (20, 30))
    hypothesis = make_multi_span((0, 10), (20, 30))

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 2
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 0
    assert summary["precision"] == 1.0
    assert summary["recall"] == 1.0
    assert summary["f1_score"] == 1.0


def test_mixed_tp_fn_fp_metrics():
    """TP=1, FN=1, FP=1 yields precision=0.5, recall=0.5, f1=0.5."""
    reference = make_multi_span((0, 10), (20, 30))
    # First hyp matches first ref; second hyp matches nothing
    hypothesis = make_multi_span((0, 10), (40, 50))

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 1
    assert summary["false_negative"] == 1
    assert summary["false_positive"] == 1
    assert summary["precision"] == 0.5
    assert summary["recall"] == 0.5
    assert summary["f1_score"] == 0.5


def test_best_fit_hypothesis_chosen():
    """When two hypothesis spans cover a reference, the one with less padding is used."""
    reference = make_span(10, 20)
    # hyp1: padding 10 (5+5), hyp2: padding 4 (2+2)
    hypothesis = {
        "detected_characteristics": [
            {
                "evidence_spans": [
                    {"start_index": 5, "end_index": 25},
                    {"start_index": 8, "end_index": 22},
                ]
            }
        ]
    }

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 1
    assert summary["undesirable_padding"]["total_excess_chars"] == 4
    ann = result["annotation_results"][0]
    assert ann["covering_hypothesis"] == {"start_index": 8, "end_index": 22}


def test_one_hypothesis_covers_multiple_references():
    """A single large hypothesis span can be TP for multiple reference spans."""
    reference = make_multi_span((5, 10), (15, 20))
    hypothesis = make_span(0, 30)

    result = evaluate_by_index(reference, hypothesis)
    summary = result["summary"]

    assert summary["true_positive"] == 2
    assert summary["false_negative"] == 0
    assert summary["false_positive"] == 0
    assert len(result["hypothesis_results"]) == 1
    assert result["hypothesis_results"][0]["label"] == "TP"


def test_extract_spans_flattens_multiple_characteristics():
    """extract_spans flattens spans across multiple detected_characteristics entries."""
    data = {
        "detected_characteristics": [
            {"evidence_spans": [{"start_index": 0, "end_index": 5}]},
            {"evidence_spans": [{"start_index": 10, "end_index": 15}]},
        ]
    }

    spans = extract_spans(data)

    assert len(spans) == 2
    assert spans[0] == {"start_index": 0, "end_index": 5}
    assert spans[1] == {"start_index": 10, "end_index": 15}


def test_extract_spans_filters_incomplete_indices():
    """extract_spans skips spans where start_index or end_index is absent or None."""
    data = {
        "detected_characteristics": [
            {
                "evidence_spans": [
                    {"start_index": 0, "end_index": 5},  # valid
                    {"start_index": None, "end_index": 5},  # None start — filtered
                    {"end_index": 5},  # missing start — filtered
                    {"start_index": 0},  # missing end — filtered
                ]
            }
        ]
    }

    spans = extract_spans(data)

    assert len(spans) == 1
    assert spans[0] == {"start_index": 0, "end_index": 5}

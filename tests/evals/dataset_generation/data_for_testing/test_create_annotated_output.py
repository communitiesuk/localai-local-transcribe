from evals.dataset_generation.data_for_testing.src.annotate import create_annotated_output


def test_empty_manual_list():
    result = create_annotated_output([], "some transcript text")

    assert result["version"] == "1.0"
    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert spans == []


def test_single_text_found_once():
    transcript = "The planning committee met on Monday."
    result = create_annotated_output(["planning committee"], transcript)

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert len(spans) == 1
    assert spans[0]["text"] == "planning committee"
    assert spans[0]["start_index"] == transcript.index("planning committee")
    assert spans[0]["end_index"] == transcript.index("planning committee") + len("planning committee")


def test_text_found_multiple_times():
    transcript = "yes and yes again yes"
    result = create_annotated_output(["yes"], transcript)

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert len(spans) == 3


def test_duplicate_entries_in_manual_list_are_deduplicated():
    transcript = "hello world"
    result = create_annotated_output(["hello", "hello", "hello"], transcript)

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert len(spans) == 1


def test_text_not_in_transcript_produces_no_span():
    result = create_annotated_output(["absent phrase"], "completely different text")

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert spans == []


def test_output_structure():
    result = create_annotated_output(["word"], "a word here")

    assert result["version"] == "1.0"
    chars = result["detected_characteristics"]
    assert len(chars) == 1
    assert chars[0]["characteristic"] == "manual_annotation"
    assert chars[0]["attribute_value"] == "manually identified"
    assert "evidence_spans" in chars[0]

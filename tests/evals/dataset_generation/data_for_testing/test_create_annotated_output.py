from evals.dataset_generation.data_for_testing.src.annotate import create_annotated_output


def _entry(text: str, category: str = "Race", value: str = "Asian") -> dict:
    return {"text": text, "category": category, "value": value}


def test_empty_manual_list():
    result = create_annotated_output([], "some transcript text")

    assert result["version"] == "1.0"
    assert result["detected_characteristics"] == []


def test_single_text_found_once():
    transcript = "The planning committee met on Monday."
    result = create_annotated_output([_entry("planning committee")], transcript)

    chars = result["detected_characteristics"]
    assert len(chars) == 1
    spans = chars[0]["evidence_spans"]
    assert len(spans) == 1
    assert spans[0]["text"] == "planning committee"
    assert spans[0]["start_index"] == transcript.index("planning committee")
    assert spans[0]["end_index"] == transcript.index("planning committee") + len("planning committee")


def test_text_found_multiple_times():
    transcript = "yes and yes again yes"
    result = create_annotated_output([_entry("yes")], transcript)

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert len(spans) == 3


def test_duplicate_entries_in_manual_list_are_deduplicated():
    transcript = "hello world"
    entries = [_entry("hello"), _entry("hello"), _entry("hello")]
    result = create_annotated_output(entries, transcript)

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert len(spans) == 1


def test_text_not_in_transcript_produces_no_span():
    result = create_annotated_output([_entry("absent phrase")], "completely different text")

    spans = result["detected_characteristics"][0]["evidence_spans"]
    assert spans == []


def test_output_structure():
    result = create_annotated_output([_entry("word", "Race", "Asian")], "a word here")

    assert result["version"] == "1.0"
    chars = result["detected_characteristics"]
    assert len(chars) == 1
    assert chars[0]["characteristic"] == "Race"
    assert chars[0]["attribute_value"] == "Asian"
    assert "evidence_spans" in chars[0]


def test_entries_grouped_by_category_and_value():
    transcript = "Alice and Bob went to the mosque"
    entries = [
        {"text": "Alice", "category": "Sex", "value": "Female"},
        {"text": "Bob", "category": "Sex", "value": "Male"},
        {"text": "mosque", "category": "Religion or Belief", "value": "Islam"},
    ]
    result = create_annotated_output(entries, transcript)

    chars = result["detected_characteristics"]
    categories = {(c["characteristic"], c["attribute_value"]) for c in chars}
    assert ("Sex", "Female") in categories
    assert ("Sex", "Male") in categories
    assert ("Religion or Belief", "Islam") in categories
    assert len(chars) == 3

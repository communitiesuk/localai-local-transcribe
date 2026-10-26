from __future__ import annotations

import pytest

from common.services.transcription_services.azure_stt_base import convert_to_dialogue_entries


def _phrase(**overrides) -> dict:
    return {"speaker": 1, "text": "hello", "offsetMilliseconds": 1500, "durationMilliseconds": 2000, **overrides}


def test_millisecond_offsets_become_second_timestamps():
    [entry] = convert_to_dialogue_entries([_phrase()])

    assert entry == {"speaker": "1", "text": "hello", "start_time": 1.5, "end_time": 3.5}


def test_speaker_labels_are_normalised_to_strings():
    [numeric], [textual] = (convert_to_dialogue_entries([_phrase(speaker=speaker)]) for speaker in (2, "Guest-1"))

    assert numeric["speaker"] == "2"
    assert textual["speaker"] == "Guest-1"


def test_confidence_is_kept_when_the_service_scores_a_phrase():
    [entry] = convert_to_dialogue_entries([_phrase(confidence=0.82)])

    assert entry["confidence"] == pytest.approx(0.82)


@pytest.mark.parametrize("phrase", [_phrase(), _phrase(confidence=None)], ids=["absent", "explicit_null"])
def test_unscored_phrases_carry_no_confidence_key(phrase):
    # An unscored phrase must stay distinguishable from one the service scored as zero.
    [entry] = convert_to_dialogue_entries([phrase])

    assert "confidence" not in entry


def test_zero_confidence_is_kept_rather_than_treated_as_missing():
    [entry] = convert_to_dialogue_entries([_phrase(confidence=0.0)])

    assert entry["confidence"] == 0.0


def test_string_numerics_from_the_service_are_coerced():
    [entry] = convert_to_dialogue_entries(
        [_phrase(offsetMilliseconds="1000", durationMilliseconds="500", confidence="0.5")]
    )

    assert (entry["start_time"], entry["end_time"], entry["confidence"]) == (1.0, 1.5, 0.5)


def test_phrase_order_is_preserved():
    phrases = [_phrase(text=str(index), offsetMilliseconds=index * 1000) for index in range(3)]

    entries = convert_to_dialogue_entries(phrases)

    assert [entry["text"] for entry in entries] == ["0", "1", "2"]
    assert [entry["start_time"] for entry in entries] == [0.0, 1.0, 2.0]


def test_no_phrases_yields_no_entries():
    assert convert_to_dialogue_entries([]) == []


@pytest.mark.parametrize("missing", ["speaker", "text", "offsetMilliseconds", "durationMilliseconds"])
def test_a_phrase_missing_a_required_field_is_an_error(missing):
    phrase = _phrase()
    del phrase[missing]

    with pytest.raises(KeyError):
        convert_to_dialogue_entries([phrase])

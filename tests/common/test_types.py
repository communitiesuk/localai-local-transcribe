from common.types import MinuteAndHallucinations


def test_minute_and_hallucinations_strips_boundary_metadata_from_text():
    result = MinuteAndHallucinations(
        text=("BEGIN meeting-summary 05f5b6d9\n" "<p>Meeting content [1].</p>\n" "END meeting-summary 05f5b6d9"),
        total_claims=0,
        hallucinations=[],
    )

    assert result.text == "<p>Meeting content [1].</p>"

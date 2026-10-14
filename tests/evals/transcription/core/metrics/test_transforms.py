from __future__ import annotations

import pytest

from evals.transcription.src.core.metrics import normalise_text


@pytest.mark.parametrize(
    ("input_text", "expected"),
    [
        ("", ""),
        ("  Hello,   WORLD!!  ", "hello world"),
    ],
)
def test_normalise_text_edge_cases(input_text, expected):
    assert normalise_text(input_text) == expected

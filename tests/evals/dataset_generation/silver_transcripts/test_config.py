from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from evals.dataset_generation.silver_transcripts.src.config import SilverTranscriptConfig


def test_config_accepts_the_generation_directories() -> None:
    config = SilverTranscriptConfig.model_validate({"input_dir": "../input/smoke", "work_dir": "../output/smoke"})

    assert config.input_dir == Path("../input/smoke")
    assert config.work_dir == Path("../output/smoke")


def test_export_directory_is_rejected() -> None:
    with pytest.raises(ValidationError):
        SilverTranscriptConfig.model_validate({"work_dir": "../output/smoke", "output_dir": "../exported"})


def test_missing_input_is_left_for_cli_validation() -> None:
    config = SilverTranscriptConfig.model_validate({"work_dir": "../output/smoke"})

    assert config.input_dir is None


def test_unknown_keys_are_rejected() -> None:
    with pytest.raises(ValidationError):
        SilverTranscriptConfig.model_validate({"input_dir": "../input/smoke", "unexpected": "value"})


@pytest.mark.parametrize("cutoff", [0, -1, float("inf"), float("nan")])
def test_invalid_cutoff_is_rejected(cutoff):
    with pytest.raises(ValidationError):
        SilverTranscriptConfig(cutoff_seconds=cutoff)

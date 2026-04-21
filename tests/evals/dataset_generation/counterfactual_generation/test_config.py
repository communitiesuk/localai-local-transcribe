from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from pydantic import ValidationError

from evals.dataset_generation.counterfactual_generation.src.config import (
    AxisDefinition,
    CounterfactualConfig,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


def test_axis_definition_initialization():
    axis_def = AxisDefinition(
        axis=ProtectedCharacteristic.SEX,
        original_value="male",
        target_value="female",
        instructions="Focus on pronouns",
    )
    assert axis_def.axis == ProtectedCharacteristic.SEX
    assert axis_def.original_value == "male"
    assert axis_def.target_value == "female"
    assert axis_def.instructions == "Focus on pronouns"


def test_axis_definition_optional_instructions():
    axis_def = AxisDefinition(
        axis=ProtectedCharacteristic.AGE,
        original_value="young",
        target_value="senior",
    )
    assert axis_def.instructions is None


def test_counterfactual_config_initialization():
    config = CounterfactualConfig(
        transcript_path="input/transcript.json",
        axes=[
            AxisDefinition(
                axis=ProtectedCharacteristic.SEX,
                original_value="male",
                target_value="female",
            )
        ],
    )
    assert config.transcript_path == "input/transcript.json"
    assert len(config.axes) == 1
    assert config.characteristic_detection_path is None


def test_counterfactual_config_with_detection_path():
    config = CounterfactualConfig(
        transcript_path="input/transcript.json",
        characteristic_detection_path="input/detection.json",
        axes=[
            AxisDefinition(
                axis=ProtectedCharacteristic.RACE,
                original_value="white",
                target_value="black",
            )
        ],
    )
    assert config.characteristic_detection_path == "input/detection.json"


def test_counterfactual_config_requires_at_least_one_axis():
    with pytest.raises(ValidationError):
        CounterfactualConfig(
            transcript_path="input/transcript.json",
            axes=[],
        )


def test_counterfactual_config_multiple_axes():
    config = CounterfactualConfig(
        transcript_path="input/transcript.json",
        axes=[
            AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female"),
            AxisDefinition(axis=ProtectedCharacteristic.AGE, original_value="young", target_value="senior"),
        ],
    )
    assert len(config.axes) == 2


def test_get_transcript_path_relative():
    with TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        config = CounterfactualConfig(
            transcript_path="input/transcript.json",
            axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")],
        )
        result = config.get_transcript_path(base_dir)
        assert result == base_dir / "input/transcript.json"


def test_get_transcript_path_absolute():
    with TemporaryDirectory() as tmpdir:
        absolute_path = Path(tmpdir) / "transcript.json"
        config = CounterfactualConfig(
            transcript_path=str(absolute_path),
            axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")],
        )
        result = config.get_transcript_path(Path("/some/base"))
        assert result == absolute_path


def test_get_characteristic_detection_path_none():
    config = CounterfactualConfig(
        transcript_path="input/transcript.json",
        axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")],
    )
    result = config.get_characteristic_detection_path(Path("/base"))
    assert result is None


def test_get_characteristic_detection_path_relative():
    with TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        config = CounterfactualConfig(
            transcript_path="input/transcript.json",
            characteristic_detection_path="input/detection.json",
            axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")],
        )
        result = config.get_characteristic_detection_path(base_dir)
        assert result == base_dir / "input/detection.json"


def test_get_characteristic_detection_path_absolute():
    with TemporaryDirectory() as tmpdir:
        absolute_path = Path(tmpdir) / "detection.json"
        config = CounterfactualConfig(
            transcript_path="input/transcript.json",
            characteristic_detection_path=str(absolute_path),
            axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")],
        )
        result = config.get_characteristic_detection_path(Path("/some/base"))
        assert result == absolute_path


def test_counterfactual_config_requires_transcript_path():
    with pytest.raises(ValidationError):
        CounterfactualConfig(
            axes=[AxisDefinition(axis=ProtectedCharacteristic.SEX, original_value="male", target_value="female")]
        )

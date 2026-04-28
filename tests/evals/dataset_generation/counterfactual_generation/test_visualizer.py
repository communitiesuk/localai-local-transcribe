from pathlib import Path
from tempfile import TemporaryDirectory

from common.database.postgres_models import DialogueEntry
from evals.dataset_generation.counterfactual_generation.src.models import (
    AxisChange,
    CounterfactualOutput,
    TranscriptInput,
)
from evals.dataset_generation.counterfactual_generation.src.visualizer import (
    _compute_text_diff,
    generate_modification_report,
)
from evals.dataset_generation.shared_constants import ProtectedCharacteristic


def test_compute_text_diff() -> None:
    identical_orig = "This is the same text"
    identical_new = "This is the same text"
    orig_result, new_result = _compute_text_diff(identical_orig, identical_new)
    assert orig_result == identical_orig
    assert new_result == identical_new

    single_diff_orig = "The quick brown fox"
    single_diff_new = "The fast brown fox"
    orig_result, new_result = _compute_text_diff(single_diff_orig, single_diff_new)
    assert '<mark class="removed">quick</mark>' in orig_result
    assert '<mark class="added">fast</mark>' in new_result
    assert "The" in orig_result
    assert "brown fox" in new_result

    multi_diff_orig = "The quick brown fox jumps"
    multi_diff_new = "The fast red fox leaps"
    orig_result, new_result = _compute_text_diff(multi_diff_orig, multi_diff_new)
    assert '<mark class="removed">' in orig_result
    assert '<mark class="added">' in new_result


def test_generate_modification_report() -> None:
    with TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "report.html"

        original_entries = [
            DialogueEntry(speaker="A", text="He is a male doctor", start_time=0.0, end_time=1.0),
            DialogueEntry(speaker="B", text="Second", start_time=1.0, end_time=2.0),
            DialogueEntry(speaker="C", text="Third", start_time=2.0, end_time=3.0),
        ]
        rewritten_entries = [
            DialogueEntry(speaker="A", text="She is a female doctor", start_time=0.0, end_time=1.0),
            DialogueEntry(speaker="B", text="Second", start_time=1.0, end_time=2.0),
            DialogueEntry(speaker="C", text="Modified Third", start_time=2.0, end_time=3.0),
        ]

        original_transcript = TranscriptInput(dialogue_entries=original_entries)
        axis_change = AxisChange(
            axis=ProtectedCharacteristic.SEX,
            original_value="male",
            target_value="female",
        )
        output = CounterfactualOutput(
            original_transcript=original_transcript,
            rewritten_transcript=rewritten_entries,
            axis_change=axis_change,
            model_version="test",
            prompt_version="v1.0",
            evidence_spans_modified=[0, 2],
        )

        generate_modification_report(output, output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "<!DOCTYPE html>" in content or "<html" in content.lower()
        assert "male" in content.lower()
        assert "female" in content.lower()
        assert str(len(original_entries)) in content

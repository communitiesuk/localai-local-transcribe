from unittest.mock import patch

import pytest

from evals.shared.blob_input import main, stage_transcription_input_prefix


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [(None, "transcription/"), ("", "transcription/"), ("transcription/demo", "transcription/demo")],
)
def test_stages_transcription_prefix(tmp_path, prefix, expected):
    with (
        patch("evals.shared.blob_input.EvalBlobStorage.from_account_urls") as storage,
        patch("evals.shared.blob_input.stage_dataset_prefix", return_value=tmp_path) as stage,
    ):
        result = stage_transcription_input_prefix(destination_dir=tmp_path, prefix=prefix)

    stage.assert_called_once_with(storage.return_value, expected, tmp_path)
    assert result == tmp_path


def test_cli_refuses_to_replace_existing_files(tmp_path, monkeypatch):
    existing = tmp_path / "existing.mp3"
    existing.write_bytes(b"keep")
    monkeypatch.setattr("sys.argv", ["blob_input", "--destination", str(tmp_path)])

    with pytest.raises(ValueError, match="Destination must be empty"):
        main()

    assert existing.read_bytes() == b"keep"

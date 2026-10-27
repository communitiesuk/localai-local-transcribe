from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile

from evals.dataset_generation.silver_transcripts.src.pipeline import SilverTranscriptPipeline
from tests.evals.dataset_generation.silver_transcripts.support import DraftAdapter


def _copy_cut(source: Path, destination: Path, _start: float, _end: float) -> None:
    """Stand in for cut_audio so segment logic can be tested without ffmpeg."""
    shutil.copyfile(source, destination)


@pytest.fixture
def draft_setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, SilverTranscriptPipeline, DraftAdapter]:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    soundfile.write(input_dir / "sample.wav", np.zeros(16000), 16000)
    monkeypatch.setattr("evals.dataset_generation.silver_transcripts.src.pipeline.convert_to_mp3", shutil.copyfile)
    adapter = DraftAdapter()
    pipeline = SilverTranscriptPipeline(tmp_path / "work", adapter)
    # Patched on the class, not the instance, so it also covers the pipeline main() builds itself.
    # Tests that exercise real encoding restore it and skip when ffmpeg is absent.
    monkeypatch.setattr(SilverTranscriptPipeline, "cut_audio", staticmethod(_copy_cut))
    return input_dir, pipeline, adapter

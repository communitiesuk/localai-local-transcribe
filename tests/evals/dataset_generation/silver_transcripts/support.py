from __future__ import annotations

from pathlib import Path

from evals.transcription.src.adapters.base import EvalsTranscriptionAdapter
from evals.transcription.src.models import TranscriptionResult

DRAFT_TEXT = "the original draft"


def result_factory(text: str = DRAFT_TEXT, **overrides: object) -> TranscriptionResult:
    entries = [{"speaker": "1", "text": text, "start_time": 0.0, "end_time": 1.0}]
    return TranscriptionResult(
        **{"text": text, "duration_sec": 0.25, "debug_info": {}, "dialogue_entries": entries, **overrides}
    )


class DraftAdapter(EvalsTranscriptionAdapter):
    def __init__(self, fail: bool = False):
        self.calls = 0
        self.fail = fail

    @property
    def name(self) -> str:
        return "test_engine"

    def transcribe(self, wav_path: str) -> TranscriptionResult:
        assert Path(wav_path).is_file()
        self.calls += 1
        if self.fail:
            return result_factory("", debug_info={"error": "service failed"})
        return result_factory()

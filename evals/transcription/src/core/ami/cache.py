import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from evals.transcription.src.core.audio_cache import AudioFileHandler, CorruptAudioError
from evals.transcription.src.models import MeetingSegment

DIARIZATION_SUFFIX = "_ref_diarization.json"
TRANSCRIPT_SUFFIX = ".txt"


class CorruptCacheEntryError(RuntimeError):
    """
    Raised when a cache entry is present but cannot be read back.
    """


@dataclass(eq=False)
class AMICacheEntry:
    """
    The three artefacts that make up one cached AMI meeting.
    """

    audio: np.ndarray
    text: str
    reference_diarization: list[dict]
    sample_rate: int


class AMISampleCache:
    """
    One cached AMI meeting: mixed audio, transcript, and reference diarization.

    All three artefacts are written and read together, so a missing one makes the entry
    incomplete and the loader rebuilds it.

    Rebuilds remove all three files before writing audio, transcript, then diarization JSON.
    Interruptions before the final write leave an incomplete entry. A partial final JSON
    raises CorruptCacheEntryError. Audio and transcript truncation alone may be readable;
    presence checks do not validate their lengths. Writes are not safe for concurrent rebuilds.
    """

    def __init__(
        self,
        processed_dir: Path,
        segment: MeetingSegment,
        index: int,
        audio_cache: AudioFileHandler | None = None,
    ):
        """
        Derives the cache paths for one meeting segment from its id, position, and cutoff.

        The cutoff is part of the key because it decides how much of the meeting is written.
        Keying on id and position alone lets a run with sample_duration_fraction set and a
        run without it collide on one filename: the second finds a complete, self-consistent
        entry and silently scores the first run's truncated audio as a whole meeting.
        Preserve the full float precision because even nearby cutoffs can select different utterances.
        """
        self._audio_cache = audio_cache if audio_cache is not None else AudioFileHandler()

        cutoff = "full" if segment.utterance_cutoff_time is None else f"c{segment.utterance_cutoff_time!r}"
        stem = f"{segment.meeting_id}_{index:06d}_{cutoff}"
        self.audio = processed_dir / f"{stem}{self._audio_cache.suffix}"
        self.transcript = processed_dir / f"{stem}{TRANSCRIPT_SUFFIX}"
        self.diarization = processed_dir / f"{stem}{DIARIZATION_SUFFIX}"

    def is_complete(self) -> bool:
        """
        Checks that every artefact of this entry is present.
        """
        return self._audio_cache.contains(self.audio) and self.transcript.is_file() and self.diarization.is_file()

    def read(self) -> AMICacheEntry:
        """
        Loads all three artefacts of this cache entry.

        Raises CorruptCacheEntryError for decoding or malformed JSON errors. Partially
        truncated audio and text can still decode successfully; no length check is performed.
        Filesystem access errors propagate without advice to delete a healthy entry.
        """
        try:
            audio, sample_rate = self._audio_cache.read(self.audio)
            return AMICacheEntry(
                audio=audio,
                sample_rate=sample_rate,
                text=self.transcript.read_text(encoding="utf-8"),
                reference_diarization=json.loads(self.diarization.read_text(encoding="utf-8")),
            )
        except (CorruptAudioError, json.JSONDecodeError, UnicodeDecodeError) as error:
            message = (
                f"Cached entry {self.audio.stem} is present but unreadable ({error}). "
                f"Delete these files to rebuild only this entry: {self.audio}, {self.transcript}, {self.diarization}."
            )
            raise CorruptCacheEntryError(message) from error

    def write(self, audio: np.ndarray, sample_rate: int, text: str, reference_diarization: list[dict]) -> None:
        """
        Invalidates the entry, then saves audio, transcript, and self-validating JSON last.
        """
        for path in (self.audio, self.transcript, self.diarization):
            path.unlink(missing_ok=True)
        self._audio_cache.write(self.audio, audio, sample_rate)
        self.transcript.write_text(text, encoding="utf-8")
        self.diarization.write_text(json.dumps(reference_diarization), encoding="utf-8")

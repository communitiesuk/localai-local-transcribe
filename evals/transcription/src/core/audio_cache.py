"""
Stores processed dataset audio on disk in a single shared format.
"""

import tempfile
from pathlib import Path
from typing import ClassVar, cast

import numpy as np
import soundfile

from common.audio.ffmpeg import convert_to_mp3


class CorruptAudioError(RuntimeError):
    """Raised when an audio file exists but cannot be decoded."""


class AudioFileHandler:
    """
    Reads and writes processed dataset audio as mono MP3.

    Owning the on-disk format in one place keeps every dataset's cached audio identical in
    encoding, so transcription results stay comparable across datasets and runs.
    """

    suffix: ClassVar[str] = ".mp3"

    def contains(self, path: Path) -> bool:
        """
        Checks whether a cached audio file exists at the given path.

        Presence only. Writes publish the final file only after conversion succeeds.
        Older or externally truncated MP3s may still decode with fewer samples;
        neither this check nor read verifies the expected duration.
        """
        return path.is_file()

    def read(self, path: Path) -> tuple[np.ndarray, int]:
        """
        Loads audio samples and returns their decoded sample rate alongside the array.

        Raises CorruptAudioError when the file exists but cannot be decoded, so callers
        do not have to know which audio library produced the failure.

        A pre-flight open surfaces initial filesystem failures as OSError. Decode by path
        so libsndfile uses native IO; file-handle callbacks can swallow mid-read IO errors.
        Decode-time failures reported by libsndfile still surface as CorruptAudioError.
        """
        with path.open("rb"):
            pass
        try:
            audio, sample_rate = soundfile.read(path)
        except soundfile.SoundFileError as error:
            message = f"Could not decode audio at {path}: {error}"
            raise CorruptAudioError(message) from error
        return cast("np.ndarray", audio), int(sample_rate)

    def write(self, path: Path, audio: np.ndarray, sample_rate: int) -> None:
        """
        Write mono MP3 through a sibling temporary file, then atomically replace the destination.
        A failed conversion leaves the previous destination intact, or absent for a new file.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

        try:
            soundfile.write(temp_path, audio, sample_rate, subtype="PCM_16")
            with tempfile.NamedTemporaryFile(
                dir=path.parent, prefix=f".{path.stem}-", suffix=self.suffix, delete=False
            ) as output_file:
                output_temp_path = Path(output_file.name)
            try:
                convert_to_mp3(temp_path, output_temp_path)
                output_temp_path.replace(path)
            finally:
                output_temp_path.unlink(missing_ok=True)
        finally:
            temp_path.unlink(missing_ok=True)

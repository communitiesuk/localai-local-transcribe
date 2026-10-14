"""Load ordinary audio files paired with same-name UTF-8 reference transcripts."""

from pathlib import Path

import soundfile

from evals.transcription.src.core.benchmark_dataset_source import BenchmarkDatasetSource
from evals.transcription.src.models import AudioSample, DatasetItem, DatasetRequest

AUDIO_SUFFIXES = {".wav", ".flac", ".ogg", ".mp3"}


class AudioFilesDataset:
    """
    Ordered audio/text pairs, with audio decoded on access.
    """

    supports_diarization = False
    dataset_split = None

    def __init__(self, input_dir: Path, num_samples: int | None = None):
        if not input_dir.is_dir():
            raise NotADirectoryError(input_dir)
        if num_samples is not None and num_samples <= 0:
            msg = "num_samples must be greater than zero"
            raise ValueError(msg)
        self.paths = sorted(p for p in input_dir.rglob("*") if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES)
        if not self.paths:
            msg = f"No supported audio files found in {input_dir}"
            raise ValueError(msg)
        if num_samples is not None:
            self.paths = self.paths[:num_samples]
        self.dataset_version = f"audio_files:{input_dir.resolve()}"
        # Read all selected references before any requests are made.
        self.references = []
        for audio_path in self.paths:
            reference_path = audio_path.with_suffix(".txt")
            try:
                self.references.append(reference_path.read_text(encoding="utf-8").strip())
            except FileNotFoundError as error:
                message = f"Missing reference transcript {reference_path} for audio file {audio_path}"
                raise FileNotFoundError(message) from error

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> DatasetItem:
        if index < 0 or index >= len(self):
            raise IndexError(index)
        path = self.paths[index]
        audio, sample_rate = soundfile.read(path, dtype="float32")
        return DatasetItem(
            audio=AudioSample(array=audio, sampling_rate=sample_rate, path=str(path.resolve())),
            text=self.references[index],
        )


class AudioFilesSource(BenchmarkDatasetSource):
    """Load local audio/reference pairs from the configured source directory."""

    name = "audio_files"
    default_subdir = "custom"

    def _load(self, request: DatasetRequest) -> AudioFilesDataset:
        return AudioFilesDataset(self.cache_dir, request.num_samples)

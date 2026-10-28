"""Load ordinary audio files paired with same-name UTF-8 reference transcripts."""

import json
import re
from pathlib import Path

import soundfile

from evals.transcription.src.core.benchmark_dataset_source import BenchmarkDatasetSource
from evals.transcription.src.models import AudioFilesDatasetSample, AudioSample, DatasetRequest

AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".webm", ".wma"}
DIARIZED_LINE_PREFIX = re.compile(r"^\s*Speaker [^:\r\n]+:\s*", re.IGNORECASE)


def _reference_text(path: Path) -> str:
    """Read a reference, removing generated speaker labels when every line is diarized."""
    text = path.read_text(encoding="utf-8").strip()
    lines = text.splitlines()
    content_lines = [line for line in lines if line.strip()]
    if content_lines and all(DIARIZED_LINE_PREFIX.match(line) for line in content_lines):
        return "\n".join(DIARIZED_LINE_PREFIX.sub("", line, count=1) for line in lines).strip()
    return text


class AudioFilesDataset:
    """Ordered audio/text pairs, with audio decoded on access."""

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
        self.references: list[str] = []
        self.diarizations: list[list[dict]] = []
        for audio_path in self.paths:
            reference_path = audio_path.with_suffix(".txt")
            try:
                self.references.append(_reference_text(reference_path))
            except FileNotFoundError as error:
                message = f"Missing reference transcript {reference_path} for audio file {audio_path}"
                raise FileNotFoundError(message) from error
            diarization_path = audio_path.with_name(f"{audio_path.stem}_ref_diarization.json")
            if diarization_path.is_file():
                data = json.loads(diarization_path.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    msg = f"Reference diarization must be a list: {diarization_path}"
                    raise TypeError(msg)
                self.diarizations.append(data)
            else:
                self.diarizations.append([])
        self.supports_diarization = all(self.diarizations)

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, index: int) -> AudioFilesDatasetSample:
        if index < 0 or index >= len(self):
            raise IndexError(index)
        path = self.paths[index]
        audio, sample_rate = soundfile.read(path, dtype="float32")
        return AudioFilesDatasetSample(
            audio=AudioSample(array=audio, sampling_rate=sample_rate, path=str(path.resolve())),
            text=self.references[index],
            file_id=path.stem,
            dataset_index=index,
            reference_diarization=self.diarizations[index],
        )


class AudioFilesSource(BenchmarkDatasetSource):
    """Load local audio/reference pairs from the configured source directory."""

    name = "audio_files"
    default_subdir = "custom"

    def _load(self, request: DatasetRequest) -> AudioFilesDataset:
        return AudioFilesDataset(self.cache_dir, request.num_samples)

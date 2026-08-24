from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common.constants import TARGET_SAMPLE_RATE
from evals.transcription.src.models import AudioFilesDatasetSample, AudioSample

AUDIO_SUFFIXES = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".wav", ".webm", ".wma"}


class AudioFilesDataset:
    def __init__(self, samples: list[AudioFilesDatasetSample]) -> None:
        self._samples = samples

    @property
    def dataset_version(self) -> str:
        return "audio_files_v0"

    @property
    def dataset_split(self) -> str | None:
        return f"n{len(self._samples)}"

    def __len__(self) -> int:
        return len(self._samples)

    def __getitem__(self, index: int) -> AudioFilesDatasetSample:
        return self._samples[index]


def load_audio_files_dataset(input_dir: Path, limit: int | None = None) -> AudioFilesDataset:
    audio_paths = sorted(path for path in input_dir.rglob("*") if path.suffix.lower() in AUDIO_SUFFIXES)
    if limit is not None:
        audio_paths = audio_paths[:limit]
    if not audio_paths:
        msg = f"No audio files found in {input_dir}"
        raise ValueError(msg)
    return AudioFilesDataset([_sample_from_audio(path, idx) for idx, path in enumerate(audio_paths)])


def _sample_from_audio(audio_path: Path, index: int) -> AudioFilesDatasetSample:
    transcript_path = audio_path.with_suffix(".txt")
    if not transcript_path.is_file():
        msg = f"Missing reference transcript: {transcript_path}"
        raise FileNotFoundError(msg)

    text = transcript_path.read_text(encoding="utf-8").strip()
    diarization = _load_diarization(audio_path, text)
    return AudioFilesDatasetSample(
        audio=AudioSample(
            array=np.array([], dtype=np.float32),
            sampling_rate=TARGET_SAMPLE_RATE,
            path=str(audio_path),
        ),
        text=text,
        file_id=audio_path.stem,
        dataset_index=index,
        reference_diarization=diarization,
    )


def _load_diarization(audio_path: Path, text: str) -> list[dict]:
    diarization_path = audio_path.with_name(f"{audio_path.stem}_ref_diarization.json")
    if diarization_path.is_file():
        with diarization_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            msg = f"Reference diarization must be a list: {diarization_path}"
            raise TypeError(msg)
        return data
    return [{"speaker": "Speaker 1", "text": text, "start_time": 0.0, "end_time": 0.0}]

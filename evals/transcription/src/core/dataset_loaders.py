from __future__ import annotations

from pathlib import Path
from typing import Protocol

from evals.transcription.src.core.audio_files_dataset import load_audio_files_dataset
from evals.transcription.src.core.dataset import load_benchmark_dataset
from evals.transcription.src.models import DatasetProtocol


class DatasetLoader(Protocol):
    name: str

    @classmethod
    def load(
        cls,
        *,
        input_dir: Path | None,
        num_samples: int | None,
        sample_duration_fraction: float | None,
    ) -> DatasetProtocol:
        pass


class AmiDatasetLoader:
    name = "ami"

    @classmethod
    def load(
        cls,
        *,
        input_dir: Path | None,
        num_samples: int | None,
        sample_duration_fraction: float | None,
    ) -> DatasetProtocol:
        if input_dir is not None:
            msg = "input_dir is not supported by ami dataset loader"
            raise ValueError(msg)
        return load_benchmark_dataset(
            num_samples=num_samples,
            sample_duration_fraction=sample_duration_fraction,
        )


class AudioFilesDatasetLoader:
    name = "audio_files"

    @classmethod
    def load(
        cls,
        *,
        input_dir: Path | None,
        num_samples: int | None,
        sample_duration_fraction: float | None,
    ) -> DatasetProtocol:
        if input_dir is None:
            msg = "input_dir is required for audio_files dataset loader"
            raise ValueError(msg)
        if sample_duration_fraction is not None:
            msg = "sample_duration_fraction is not supported by audio_files dataset loader"
            raise ValueError(msg)
        return load_audio_files_dataset(input_dir, limit=num_samples)


DATASET_LOADER_REGISTRY: dict[str, type[DatasetLoader]] = {
    AmiDatasetLoader.name: AmiDatasetLoader,
    AudioFilesDatasetLoader.name: AudioFilesDatasetLoader,
}

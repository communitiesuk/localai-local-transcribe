import logging
from pathlib import Path

from evals.transcription.src.constants import (
    AUDIO_DIR,
)
from evals.transcription.src.core.ami.loader import AMIDatasetSource
from evals.transcription.src.core.audio_cache import AudioFileHandler
from evals.transcription.src.core.audio_files_dataset import AudioFilesSource
from evals.transcription.src.core.benchmark_dataset_source import BenchmarkDatasetSource
from evals.transcription.src.core.english_dialects.english_dialects_dataset import EnglishDialectsSource
from evals.transcription.src.models import DatasetItem, DatasetProtocol

logger = logging.getLogger(__name__)

DEFAULT_DATASET_NAME = AMIDatasetSource.name

DATASET_REGISTRY: dict[str, type[BenchmarkDatasetSource]] = {
    AMIDatasetSource.name: AMIDatasetSource,
    EnglishDialectsSource.name: EnglishDialectsSource,
    AudioFilesSource.name: AudioFilesSource,
}


def load_benchmark_dataset(
    num_samples: int | None,
    sample_duration_fraction: float | None = None,
    dataset_name: str = DEFAULT_DATASET_NAME,
    samples_per_group: int | None = None,
    input_dir: Path | None = None,
) -> DatasetProtocol:
    """
    Load a benchmark using the configured source/cache directory or its default.
    """
    source_class = DATASET_REGISTRY.get(dataset_name)
    if source_class is None:
        message = f"Unknown transcription dataset: {dataset_name}"
        raise ValueError(message)
    return source_class(input_dir).load(
        num_samples=num_samples,
        sample_duration_fraction=sample_duration_fraction,
        samples_per_group=samples_per_group,
    )


def prepare_audio_for_transcription(example: DatasetItem, index: int) -> str:
    """
    Converts the input audio to MP3 format using ffmpeg and caches it.
    """
    if example.audio.path and Path(example.audio.path).exists():
        return example.audio.path

    audio_data = example.audio.array
    sample_rate = example.audio.sampling_rate

    audio_cache = AudioFileHandler()
    output_path = AUDIO_DIR / f"sample_{index:06d}{audio_cache.suffix}"

    audio_cache.write(output_path, audio_data, sample_rate)

    return str(output_path)

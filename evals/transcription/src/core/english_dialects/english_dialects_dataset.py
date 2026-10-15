from __future__ import annotations

from bisect import bisect_right
from collections import defaultdict, deque
from collections.abc import Sequence
from itertools import accumulate
from pathlib import Path

import numpy as np
from datasets import Dataset, load_dataset

from evals.transcription.src.core.audio_cache import AudioFileHandler
from evals.transcription.src.core.benchmark_dataset_source import BenchmarkDatasetSource
from evals.transcription.src.models import AudioSample, DatasetRequest, EnglishDialectsSample

DATASET_NAME = "ylacombe/english_dialects"
PUBLISHED_SPLIT = "train"
ALL_SUBSETS = (
    "irish_male",
    "midlands_female",
    "midlands_male",
    "northern_female",
    "northern_male",
    "scottish_female",
    "scottish_male",
    "southern_female",
    "southern_male",
    "welsh_female",
    "welsh_male",
)


class EnglishDialectsDataset:
    """
    Indexed view over every published English Dialects subset.
    """

    supports_diarization = False

    def __init__(
        self,
        cache_dir: Path,
        subsets: Sequence[str] = ALL_SUBSETS,
        num_samples: int | None = None,
        samples_per_group: int | None = None,
    ):
        unknown = sorted(set(subsets) - set(ALL_SUBSETS))
        if unknown:
            msg = f"Unknown English Dialects subsets: {', '.join(unknown)}"
            raise ValueError(msg)
        if num_samples is not None and num_samples <= 0:
            msg = "num_samples must be greater than zero"
            raise ValueError(msg)
        if samples_per_group is not None and samples_per_group <= 0:
            msg = "samples_per_group must be greater than zero"
            raise ValueError(msg)
        if samples_per_group is not None and num_samples is not None:
            msg = "Use either samples_per_group or num_samples, not both"
            raise ValueError(msg)

        self.subsets = tuple(subsets)
        self.cache_dir = cache_dir
        self.raw_cache_dir = self.cache_dir / "raw"
        self.audio_cache = AudioFileHandler()
        self.processed_cache_dir = self.cache_dir / "processed" / "mono_mp3_v1"
        self.raw_cache_dir.mkdir(parents=True, exist_ok=True)
        self.processed_cache_dir.mkdir(parents=True, exist_ok=True)
        self.datasets: list[Dataset] = [
            load_dataset(
                DATASET_NAME,
                subset,
                split=PUBLISHED_SPLIT,
                cache_dir=str(self.raw_cache_dir),
            )
            for subset in self.subsets
        ]
        self.metadata_datasets = [
            dataset.select_columns(["text", "speaker_id", "line_id"]) for dataset in self.datasets
        ]
        if num_samples is not None:
            subset_sample_counts = [0] * len(self.datasets)
            subset_indices = sorted(
                (index for index, dataset in enumerate(self.datasets) if len(dataset)),
                key=lambda index: self.subsets[index],
            )
            # Canonicalise before shuffling so selection is independent of subset order.
            np.random.default_rng(42).shuffle(subset_indices)
            available_groups = deque(subset_indices)
            remaining_samples = num_samples
            while remaining_samples and available_groups:
                group = available_groups.popleft()
                subset_sample_counts[group] += 1
                remaining_samples -= 1
                if subset_sample_counts[group] < len(self.datasets[group]):
                    available_groups.append(group)
            self.selected_indices = [
                self._balanced_speaker_indices(dataset, count)
                for dataset, count in zip(self.datasets, subset_sample_counts, strict=True)
            ]
        else:
            self.selected_indices = [
                self._balanced_speaker_indices(dataset, samples_per_group)
                if samples_per_group is not None
                else list(range(len(dataset)))
                for dataset in self.datasets
            ]
        self.cumulative_sizes = list(accumulate(len(indices) for indices in self.selected_indices))
        total = self.cumulative_sizes[-1] if self.cumulative_sizes else 0
        self.num_samples = total
        self.samples_per_group = samples_per_group

    @staticmethod
    def _balanced_speaker_indices(dataset: Dataset, max_samples: int) -> list[int]:
        """
        Select deterministically in speaker rounds so prolific speakers do not dominate.
        """
        indices_by_speaker: dict[str, deque[int]] = defaultdict(deque)
        for index, speaker_id in enumerate(dataset["speaker_id"]):
            indices_by_speaker[str(speaker_id)].append(index)

        selected: list[int] = []
        speakers = sorted(indices_by_speaker)
        while len(selected) < min(max_samples, len(dataset)):
            added_in_round = False
            for speaker in speakers:
                if indices_by_speaker[speaker]:
                    selected.append(indices_by_speaker[speaker].popleft())
                    added_in_round = True
                    if len(selected) == min(max_samples, len(dataset)):
                        break
            if not added_in_round:
                break
        return selected

    @property
    def dataset_version(self) -> str:
        return "EnglishDialects_v1"

    @property
    def dataset_split(self) -> str:
        # The publisher only provides a train-named split. This evaluation uses all
        # of it as an evaluation corpus; it is not claimed to be unseen test data.
        return "published_train_all"

    def __len__(self) -> int:
        return self.num_samples

    def __getitem__(self, index: int) -> EnglishDialectsSample:
        if index < 0 or index >= self.num_samples:
            msg = f"Sample index {index} out of range [0, {self.num_samples})"
            raise IndexError(msg)

        dataset_index = bisect_right(self.cumulative_sizes, index)
        previous_size = self.cumulative_sizes[dataset_index - 1] if dataset_index else 0
        subset_position = index - previous_size
        source_index = self.selected_indices[dataset_index][subset_position]
        row = self.metadata_datasets[dataset_index][source_index]
        subset = self.subsets[dataset_index]
        dialect, gender = subset.rsplit("_", maxsplit=1)
        audio_path = self.processed_cache_dir / subset / f"{source_index:06d}{self.audio_cache.suffix}"
        if not audio_path.is_file():
            audio = self.datasets[dataset_index][source_index]["audio"]
            self.audio_cache.write(
                audio_path, np.asarray(audio["array"], dtype=np.float32), int(audio["sampling_rate"])
            )

        decoded_audio, decoded_sample_rate = self.audio_cache.read(audio_path)
        return EnglishDialectsSample(
            audio=AudioSample(
                array=decoded_audio,
                sampling_rate=decoded_sample_rate,
                path=str(audio_path.resolve()),
            ),
            text=str(row["text"]),
            sample_metadata={
                "group": subset,
                "dialect": dialect,
                "gender": gender,
                "speaker_id": str(row["speaker_id"]),
                "line_id": str(row["line_id"]),
                "dataset_index": index,
            },
            dialect=dialect,
            gender=gender,
            speaker_id=str(row["speaker_id"]),
            line_id=str(row["line_id"]),
            dataset_index=index,
        )


class EnglishDialectsSource(BenchmarkDatasetSource):
    """
    Load English Dialects with sampling across its published dialect/gender groups.
    """

    name = "english_dialects"
    default_subdir = "english_dialects"
    supports_samples_per_group = True

    def _load(self, request: DatasetRequest) -> EnglishDialectsDataset:
        return EnglishDialectsDataset(
            num_samples=request.num_samples,
            samples_per_group=request.samples_per_group,
            cache_dir=self.cache_dir,
        )

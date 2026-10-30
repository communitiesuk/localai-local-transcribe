import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from evals.transcription.src.constants import INPUT_DIR
from evals.transcription.src.models import DatasetProtocol, DatasetRequest

logger = logging.getLogger(__name__)


class BenchmarkDatasetSource(ABC):
    """
    Abstract base class for transcription benchmark dataset sources.

    A source owns the resolution of its dataset cache directory and declares which
    sampling options it understands, so callers can treat every dataset uniformly and
    unsupported options fail with a consistent message instead of being ignored.
    """

    name: ClassVar[str]
    default_subdir: ClassVar[str]
    supports_sample_duration_fraction: ClassVar[bool] = False
    supports_samples_per_group: ClassVar[bool] = False

    def __init__(self, input_dir: Path | None = None) -> None:
        """
        Initialises the source with a configured cache directory, or this dataset's default.
        """
        self.cache_dir = input_dir if input_dir is not None else INPUT_DIR / self.default_subdir

    def load(
        self,
        num_samples: int | None = None,
        sample_duration_fraction: float | None = None,
        samples_per_group: int | None = None,
    ) -> DatasetProtocol:
        """
        Validates the requested sampling options, then builds the dataset.
        """
        request = DatasetRequest(
            num_samples=num_samples,
            sample_duration_fraction=sample_duration_fraction,
            samples_per_group=samples_per_group,
        )
        self._reject_unsupported(
            "sample_duration_fraction", request.sample_duration_fraction, self.supports_sample_duration_fraction
        )
        self._reject_unsupported("samples_per_group", request.samples_per_group, self.supports_samples_per_group)

        logger.info("Loading %s dataset with %s samples from %s", self.name, request.num_samples, self.cache_dir)
        return self._load(request)

    def _reject_unsupported(self, option: str, value: object, supported: bool) -> None:
        """
        Raises when an option was requested that this dataset does not understand.
        """
        if value is not None and not supported:
            message = f"{self.name} does not support {option}"
            raise ValueError(message)

    @abstractmethod
    def _load(self, request: DatasetRequest) -> DatasetProtocol:
        """Build the dataset from this source's cache directory."""

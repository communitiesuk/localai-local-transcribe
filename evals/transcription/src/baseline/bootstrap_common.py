"""Shared meeting-block bootstrap helpers for AMI-proxy baseline calibration (AIILG-680).

Holds calculation helpers reused by ``wer_bootstrap.py`` and ``wder_bootstrap.py``.
These cover relative increase, bootstrap distribution summary, and meeting-block
resampling of a numerator over denominator ratio.

Meetings are the resampling unit. The helpers support uncertainty estimates for aggregates
on the baseline transcription eval config
(``evals/transcription/configs/larger_cloud_test.yaml``, 10 full audio recordings of the
Augmented Multi-party Interaction (AMI) dataset, run with Azure speech-to-text). They do
not estimate Azure run-to-run randomness.
"""

from __future__ import annotations

from typing import cast

import numpy as np

from evals.transcription.src.constants import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_QUANTILES,
    DEFAULT_RANDOM_SEED,
)


def relative_increase(value: float, baseline: float) -> float:
    """Return (value - baseline) / baseline for relative change against a baseline."""
    return (value - baseline) / baseline


def bootstrap_summary(
    bootstrap_values: np.ndarray,
    *,
    quantiles: tuple[float, ...] = DEFAULT_QUANTILES,
) -> dict[str, float | dict[str, float]]:
    """Summarise a bootstrap distribution with mean, std, and quantiles."""
    quantile_values = {
        f"p{int(quantile * 100)}": float(np.quantile(bootstrap_values, quantile)) for quantile in quantiles
    }
    return {
        "mean": float(np.mean(bootstrap_values)),
        "std": float(np.std(bootstrap_values, ddof=1)),
        "min": float(np.min(bootstrap_values)),
        "max": float(np.max(bootstrap_values)),
        "quantiles": quantile_values,
    }


def meeting_block_bootstrap_ratios(
    numerators: np.ndarray,
    denominators: np.ndarray,
    *,
    n_resamples: int = DEFAULT_BOOTSTRAP_RESAMPLES,
    random_seed: int = DEFAULT_RANDOM_SEED,
) -> np.ndarray:
    """Resample meeting blocks with replacement and return a numerator over denominator ratio per draw.

    ``numerators`` and ``denominators`` are parallel per-meeting arrays of equal length.
    Each draw samples ``len(numerators)`` meeting indices with replacement, sums both arrays
    on that draw, then divides.
    """
    meeting_count = len(numerators)
    rng = np.random.default_rng(random_seed)
    # Shape is (n_resamples, meeting_count). This is the index matrix into the meeting arrays.
    indices = rng.integers(0, meeting_count, size=(n_resamples, meeting_count))
    resampled_numerators = numerators[indices].sum(axis=1)
    resampled_denominators = denominators[indices].sum(axis=1)
    # Numpy stubs type array division as Any. Cast to match the declared return type.
    return cast("np.ndarray", resampled_numerators / resampled_denominators)

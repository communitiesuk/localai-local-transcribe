from __future__ import annotations

import logging
from pathlib import Path

import matplotlib.pyplot as plt

from evals.summarisation.src.bias.constants import VISUALIZATIONS_DIRNAME
from evals.summarisation.src.bias.types import MetricData, PlottingRecord
from evals.summarisation.src.bias.visualization.plotting import (
    create_comparison_figure,
    finalize_figure,
    plot_metric_comparison,
)

logger = logging.getLogger(__name__)


def generate_visualizations(records: list[PlottingRecord], output_dir: Path) -> None:
    """Generates and saves visualization PDFs for all plotting records."""
    viz_dir = output_dir / VISUALIZATIONS_DIRNAME
    viz_dir.mkdir(parents=True, exist_ok=True)

    for idx, record in enumerate(records):
        _create_record_visualization(record, idx, viz_dir)

    logger.info("Visualizations saved to %s", viz_dir)


def _create_record_visualization(
    rec: PlottingRecord,
    idx: int,
    output_dir: Path,
) -> None:
    """Creates and saves single comparison visualization for a plotting record."""
    all_metrics = [m.metric_name for m in rec.metrics]

    metric_data: dict[str, MetricData] = {}
    for metric in rec.metrics:
        metric_data[metric.metric_name] = MetricData(
            original_values=metric.original_values,
            cf_values=metric.counterfactual_values,
            original_mean=metric.original_mean,
            cf_mean=metric.counterfactual_mean,
        )

    fig, axes = create_comparison_figure(len(all_metrics))

    for metric_idx, (ax, metric_name) in enumerate(zip(axes, all_metrics, strict=False)):
        is_last = metric_idx == len(all_metrics) - 1
        plot_metric_comparison(ax, metric_data[metric_name], metric_name, is_last, rec.group_a_name, rec.group_b_name)

    finalize_figure(fig, axes, rec.protected_characteristic, rec.axis_of_change)

    axis_key = f"{rec.protected_characteristic}_{rec.axis_of_change}"
    prefix = "supplementary_" if rec.is_supplementary else ""
    output_path = output_dir / f"{prefix}{axis_key}_comparison_{idx}.pdf"
    plt.savefig(output_path, bbox_inches="tight")
    plt.close()

    logger.info("Generated visualization: %s", output_path.name)

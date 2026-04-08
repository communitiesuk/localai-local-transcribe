from __future__ import annotations

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from evals.summarisation.src.bias.types import MetricData
from evals.summarisation.src.bias.visualization.plot_config import LAYOUT
from evals.summarisation.src.bias.visualization.plot_elements import (
    add_data_points,
    add_mean_markers,
    add_shift_arrow,
    add_std_bands,
    add_std_legend_items,
    configure_axis_labels,
    configure_axis_limits,
)


def plot_metric_comparison(
    ax: Axes,
    metric_data: MetricData,
    metric_name: str,
    is_last: bool,
    group_a_name: str,
    group_b_name: str,
) -> None:
    """Plots comparison visualization for a single metric showing distributions and shift."""
    orig_values = metric_data["original_values"]
    cf_values = metric_data["cf_values"]
    orig_mean = metric_data["original_mean"]
    cf_mean = metric_data["cf_mean"]

    orig_std = float(np.std(orig_values))
    cf_std = float(np.std(cf_values))
    all_x_values = [*orig_values, *cf_values, orig_mean, cf_mean]

    add_std_bands(ax, orig_mean, cf_mean, orig_std, cf_std)
    add_data_points(ax, orig_values, cf_values, group_a_name, group_b_name)
    add_mean_markers(ax, orig_mean, cf_mean, group_a_name, group_b_name)
    add_std_legend_items(ax, group_a_name, group_b_name)
    add_shift_arrow(ax, orig_mean, cf_mean)
    configure_axis_limits(ax, all_x_values)
    configure_axis_labels(ax, metric_name, is_last, group_a_name, group_b_name)


def create_comparison_figure(
    num_metrics: int,
) -> tuple[plt.Figure, list[Axes]]:
    """Creates matplotlib figure with subplots for each metric comparison."""
    fig, axes = plt.subplots(
        num_metrics,
        1,
        figsize=(LAYOUT.figure_width, LAYOUT.metric_height * num_metrics),
        sharex=False,
    )

    if num_metrics == 1:
        axes = [axes]

    return fig, axes


def finalize_figure(
    fig: plt.Figure,
    axes: list[Axes],
    protected_characteristic: str,
    axis_of_change: str,
) -> None:
    """Finalizes figure with legend, title, and layout adjustments."""
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=3,
        framealpha=0.95,
        fontsize=10,
        edgecolor="black",
    )

    fig.suptitle(
        f"Bias Analysis: {protected_characteristic} - {axis_of_change}\n"
        f"(Each metric independently scaled | Arrows = shift direction)",
        fontsize=13,
        fontweight="bold",
        y=0.995,
    )

    plt.tight_layout(rect=(0, 0.03, 1, 0.99))

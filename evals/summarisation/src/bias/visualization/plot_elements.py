from __future__ import annotations

import numpy as np
from matplotlib.axes import Axes

from evals.summarisation.src.bias.visualization.plot_config import COLORS, LAYOUT, POSITIONS, SIZES


def add_std_bands(
    ax: Axes,
    orig_mean: float,
    cf_mean: float,
    orig_std: float,
    cf_std: float,
) -> None:
    """Adds shaded standard deviation bands for both groups to the plot."""
    ax.axvspan(
        orig_mean - orig_std,
        orig_mean + orig_std,
        ymin=LAYOUT.std_band_ymin_a,
        ymax=LAYOUT.std_band_ymax_a,
        color=COLORS.group_a,
        alpha=0.15,
        zorder=0,
    )
    ax.axvspan(
        cf_mean - cf_std,
        cf_mean + cf_std,
        ymin=LAYOUT.std_band_ymin_b,
        ymax=LAYOUT.std_band_ymax_b,
        color=COLORS.group_b,
        alpha=0.15,
        zorder=0,
    )


def add_data_points(
    ax: Axes,
    orig_values: list[float],
    cf_values: list[float],
    group_a_name: str,
    group_b_name: str,
) -> None:
    """Adds jittered scatter points for original and counterfactual values."""
    rng = np.random.default_rng()
    orig_y_jitter = POSITIONS.group_a_y + rng.uniform(-POSITIONS.jitter_range, POSITIONS.jitter_range, len(orig_values))
    cf_y_jitter = POSITIONS.group_b_y + rng.uniform(-POSITIONS.jitter_range, POSITIONS.jitter_range, len(cf_values))

    ax.scatter(
        orig_values,
        orig_y_jitter,
        color=COLORS.group_a,
        alpha=0.6,
        s=SIZES.scatter_point,
        label=group_a_name,
        edgecolors=COLORS.group_a_dark,
        linewidths=1.5,
        zorder=2,
    )
    ax.scatter(
        cf_values,
        cf_y_jitter,
        color=COLORS.group_b,
        alpha=0.6,
        s=SIZES.scatter_point,
        label=group_b_name,
        edgecolors=COLORS.group_b_dark,
        linewidths=1.5,
        zorder=2,
    )


def add_mean_markers(
    ax: Axes,
    orig_mean: float,
    cf_mean: float,
    group_a_name: str,
    group_b_name: str,
) -> None:
    """Adds diamond markers for mean values of both groups."""
    ax.scatter(
        orig_mean,
        POSITIONS.group_a_y,
        color=COLORS.group_a_dark,
        s=SIZES.mean_marker,
        marker="D",
        label=f"{group_a_name} Mean",
        edgecolors="black",
        linewidths=2,
        zorder=3,
    )
    ax.scatter(
        cf_mean,
        POSITIONS.group_b_y,
        color=COLORS.group_b_dark,
        s=SIZES.mean_marker,
        marker="D",
        label=f"{group_b_name} Mean",
        edgecolors="black",
        linewidths=2,
        zorder=3,
    )


def add_std_legend_items(ax: Axes, group_a_name: str, group_b_name: str) -> None:
    """Adds standard deviation legend items for both groups."""
    ax.errorbar(
        [],
        [],
        xerr=1,
        fmt="none",
        ecolor=COLORS.group_a,
        capsize=5,
        elinewidth=2,
        alpha=0.5,
        label=f"{group_a_name} ±1 Std",
    )
    ax.errorbar(
        [],
        [],
        xerr=1,
        fmt="none",
        ecolor=COLORS.group_b,
        capsize=5,
        elinewidth=2,
        alpha=0.5,
        label=f"{group_b_name} ±1 Std",
    )


def add_shift_arrow(ax: Axes, orig_mean: float, cf_mean: float) -> None:
    """Adds arrow showing shift direction from original to counterfactual mean."""
    ax.annotate(
        "",
        xy=(cf_mean, POSITIONS.group_b_y),
        xytext=(orig_mean, POSITIONS.group_a_y),
        arrowprops={
            "arrowstyle": "->",
            "color": COLORS.arrow,
            "lw": 3,
            "alpha": 0.8,
            "shrinkA": 10,
            "shrinkB": 10,
        },
        zorder=1,
    )


def configure_axis_limits(
    ax: Axes,
    all_x_values: list[float],
) -> None:
    """Configures axis limits with padding based on data range."""
    x_range = max(all_x_values) - min(all_x_values)
    padding = x_range * LAYOUT.x_padding_factor if x_range > 0 else 0.1
    ax.set_xlim(min(all_x_values) - padding, max(all_x_values) + padding)
    ax.set_ylim(0, 1)


def configure_axis_labels(
    ax: Axes,
    metric_name: str,
    is_last: bool,
    group_a_name: str,
    group_b_name: str,
) -> None:
    """Configures axis labels and grid for metric subplot."""
    ax.set_yticks([POSITIONS.group_a_y, POSITIONS.group_b_y])
    ax.set_yticklabels([group_a_name, group_b_name], fontsize=9)
    ax.set_ylabel(metric_name, fontsize=11, fontweight="bold", rotation=0, ha="right", va="center")
    ax.grid(axis="x", alpha=0.3, linestyle=":")

    if is_last:
        ax.set_xlabel("Less Favorable ← Score → More Favorable", fontsize=12, fontweight="bold")

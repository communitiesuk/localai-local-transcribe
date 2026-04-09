from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlotColors:
    """Color scheme for bias visualization plots."""

    group_a: str = "steelblue"
    group_a_dark: str = "darkblue"
    group_b: str = "coral"
    group_b_dark: str = "darkred"
    centroid: str = "purple"
    arrow: str = "gold"


@dataclass(frozen=True)
class PlotPositions:
    """Y-axis positions and jitter settings for plot elements."""

    group_a_y: float = 0.25
    group_b_y: float = 0.75
    centroid_y: float = 0.5
    jitter_range: float = 0.08


@dataclass(frozen=True)
class PlotSizes:
    """Marker and point sizes for plot elements."""

    scatter_point: int = 100
    mean_marker: int = 75
    centroid_marker: int = 300


@dataclass(frozen=True)
class PlotLayout:
    """Figure dimensions and layout parameters for plots."""

    figure_width: int = 12
    metric_height: int = 3
    x_padding_factor: float = 0.15
    std_band_ymin_a: float = 0.1
    std_band_ymax_a: float = 0.4
    std_band_ymin_b: float = 0.6
    std_band_ymax_b: float = 0.9


COLORS = PlotColors()
POSITIONS = PlotPositions()
SIZES = PlotSizes()
LAYOUT = PlotLayout()

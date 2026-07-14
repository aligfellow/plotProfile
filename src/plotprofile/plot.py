"""Reaction profile plotting."""

import colorsys
import importlib.resources as pkg_resources
import inspect
import json
import logging
from itertools import pairwise
from types import SimpleNamespace
from typing import Any, cast

import matplotlib.colors as mpc
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.font_manager import FontProperties, fontManager
from matplotlib.lines import Line2D

logger = logging.getLogger(__name__)

# Style keys that can be set per-axis. Set at the top level they apply to both axes;
# the same key inside `y1` or `y2` overrides it for that axis alone.
_SERIES_KEYS = (
    "colors",
    "curviness",
    "line_width",
    "marker_size",
    "point_type",
    "bar_length",
    "bar_width",
    "connect_bar_ends",
    "desaturate",
    "desaturate_factor",
    "linestyle",
    "dash_spacing",
)
# Either axis takes the same keys: the shared series keys, plus its own axis label.
_AXIS_KEYS = (*_SERIES_KEYS, "label")

# Gap between a value label and the point label stacked beyond it, in points.
_LABEL_GAP_POINTS = 2.0


# Every style key the plotter reads; anything else raises.
_STYLE_KEYS = frozenset(
    (
        *_SERIES_KEYS,
        "annotation_below_arrow",
        "annotation_buffer",
        "annotation_color",
        "annotation_size",
        "annotation_space",
        "annotation_style",
        "annotation_weight",
        "arrow_color",
        "arrow_width",
        "axes",
        "axis_linewidth",
        "buffer_factor",
        "energy",
        "figsize",
        "font_family",
        "font_size",
        "font_style",
        "font_weight",
        "labels",
        "legend",
        "point_label_color",
        "show_legend",
        "sig_figs",
        "square",
        "units",
        "x_indices",
        "x_label",
        "y1",
        "y2",
        "y_label",
    )
)


def _load_style(style_name):
    with pkg_resources.files("plotprofile").joinpath("styles.json").open("r") as f:
        styles = json.load(f)

    base = styles.get("default", {})
    overlay = styles.get(style_name, {})
    base.update(overlay)
    return base


def desaturate_colour(color, factor=1.2):
    """Desaturate a colour, for the fill under a curve."""
    rgb = mpc.to_rgb(color)
    hls = colorsys.rgb_to_hls(*rgb)
    hls_new = (hls[0], 1 - (0.4 * factor), 0.3 * factor)
    return colorsys.hls_to_rgb(*hls_new)


def generate_coordinates(energies):
    """Map a list of energies to (x, y) points, skipping None and centring repeats.

    A repeated value spans its indices and is placed at their midpoint; None leaves
    a gap in the x-positions rather than shifting later points left.
    """
    x_coords, y_coords = [], []
    i = 0
    while i < len(energies):
        if energies[i] is None:
            i += 1
            continue

        start_idx = i
        current_energy = energies[i]

        # Find end of consecutive non-None duplicates
        j = i + 1
        while j < len(energies) and energies[j] == current_energy and energies[j] is not None:
            j += 1

        if j - start_idx > 1:
            midpoint = (start_idx + j - 1) / 2
            x_coords.append(midpoint)
            y_coords.append(current_energy)
        else:
            x_coords.append(i)
            y_coords.append(current_energy)

        i = j
    return x_coords, y_coords


def cubic_bezier_points(p0, p1, p2, p3, num=500):
    """Sample a cubic bezier defined by control points p0-p3."""
    t = np.linspace(0, 1, num)
    return (
        ((1 - t) ** 3)[:, None] * p0
        + 3 * ((1 - t) ** 2)[:, None] * t[:, None] * p1
        + 3 * (1 - t)[:, None] * (t**2)[:, None] * p2
        + (t**3)[:, None] * p3
    )


class ReactionProfilePlotter:
    """Draws reaction profiles. Style keys come from styles.json, overridden by kwargs."""

    def __init__(self, style="default", **kwargs):
        unknown = sorted(set(kwargs) - _STYLE_KEYS)
        if unknown:
            raise TypeError(
                f"Unknown style key(s): {', '.join(map(repr, unknown))}. Valid keys: {', '.join(sorted(_STYLE_KEYS))}."
            )

        try:
            style_dict = _load_style(style)
            if not style_dict:
                logger.warning(f"Style '{style}' not found. Using default style.")
                style_dict = _load_style("default")
        except Exception as e:
            logger.warning(f"Error loading style '{style}': {e}. Using default style.")
            style_dict = _load_style("default")
        style_dict.update(kwargs)

        try:
            self.figsize = tuple(style_dict.get("figsize", (5, 4.5)))
            self.point_type = style_dict.get("point_type", "dot")
            self.curviness = float(style_dict.get("curviness", 0.42))
            self.desaturate = bool(style_dict.get("desaturate", True))
            self.desaturate_factor = float(style_dict.get("desaturate_factor", 1.2))
            # A matplotlib linestyle for every series on an axis, or a dict of them
            # keyed by series label. None is solid.
            self.linestyle = style_dict.get("linestyle", None)
            self.labels = bool(style_dict.get("labels", True))
            self.show_legend = bool(style_dict.get("show_legend", True))
            self.line_width = float(style_dict.get("line_width", 2))
            self.bar_width = float(style_dict.get("bar_width", 3))
            self.bar_length = float(style_dict.get("bar_length", 0.3))
            self.marker_size = float(style_dict.get("marker_size", 5))
            self.font_size = int(style_dict.get("font_size", 10))
            self.axes = style_dict.get("axes", "")
            self.axis_linewidth = float(style_dict.get("axis_linewidth", 1))
            self.colors = style_dict.get("colors", "viridis")
            self.arrow_color = style_dict.get("arrow_color", "black")
            self.annotation_color = style_dict.get("annotation_color", "black")
            self.buffer_factor = float(style_dict.get("buffer_factor", 0.025))
            self.energy = style_dict.get("energy", "G")
            self.units = style_dict.get("units", "kcal")
            self.annotation_space = float(style_dict.get("annotation_space", 0.01))
            self.arrow_width = float(style_dict.get("arrow_width", 1.5))
            self.annotation_buffer = float(style_dict.get("annotation_buffer", 0.0))
            self.sig_figs = int(style_dict.get("sig_figs", 1))
            self.point_label_color = style_dict.get("point_label_color", "black")
            self.annotation_below_arrow = bool(style_dict.get("annotation_below_arrow", False))
            self.connect_bar_ends = bool(style_dict.get("connect_bar_ends", True))
            self.dash_spacing = float(style_dict.get("dash_spacing", 2.5))
            self.x_label = style_dict.get("x_label", None)
            self.y_label = style_dict.get("y_label", None)
            self.x_indices = bool(style_dict.get("x_indices", False))
            # Keep the *axes* square, whatever the figure has to be to fit a
            # legend beside it. Without this, moving the legend out squashes the
            # plot into a rectangle.
            self.square = bool(style_dict.get("square", False))
        except Exception as e:
            logger.error(f"Invalid style parameters: {e}")
            raise ValueError(f"Invalid style parameters: {e}") from e

        # Outside the try: a bad key in these must raise, not be reported as a style error.
        self.legend = self._sub_style("legend", style_dict.get("legend"), allowed=None)
        self.y1 = self._sub_style("y1", style_dict.get("y1"), _AXIS_KEYS)
        self.y2 = self._sub_style("y2", style_dict.get("y2"), _AXIS_KEYS)

        self.font_kwargs: dict[str, Any] = {
            "fontsize": style_dict.get("font_size", 10),
        }
        self.font_properties = self._get_font_properties(style_dict)
        font_family = self.font_properties.get_family()
        font_family = font_family[0] if font_family else "sans-serif"
        self.annotation_kwargs: dict[str, Any] = {
            "fontsize": style_dict.get("annotation_size", self.font_size),
            "fontfamily": font_family,
            "fontweight": style_dict.get("annotation_weight", "semibold"),
            "fontstyle": style_dict.get("annotation_style", "italic"),
        }

    @staticmethod
    def _sub_style(name, value, allowed):
        """Validate a nested style dict (`y1`, `y2`, `legend`).

        `allowed=None` accepts any key; `legend` uses it because matplotlib validates
        its own kwargs.
        """
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise TypeError(f"'{name}' must be a dict of style overrides, got {type(value).__name__}")
        if allowed is not None:
            unknown = [key for key in value if key not in allowed]
            if unknown:
                raise TypeError(
                    f"Unknown {name} key(s): {', '.join(map(repr, unknown))}. Valid keys: {', '.join(sorted(allowed))}."
                )
        return dict(value)

    def _axis_style(self, overrides=None):
        """Effective style for one axis: the shared style keys, with `overrides` applied."""
        style = {key: getattr(self, key) for key in _SERIES_KEYS}
        style["label"] = self.y_label
        style.update(overrides or {})
        return SimpleNamespace(**style)

    @staticmethod
    def _line_kwargs(st, label):
        """Line kwargs for one series, resolving `linestyle` to matplotlib's.

        Solid and '--' use the package's own dash, scaled to the line and spaced by
        `dash_spacing`. Any other spec is passed to matplotlib as given.
        """
        spec = st.linestyle
        if isinstance(spec, dict):
            spec = spec.get(label)
        base = {"dash_capstyle": "round"}
        if spec is None or spec in ("solid", "-"):
            return {**base, "linestyle": "solid", "dashes": (st.line_width, 0)}
        if spec in ("dashed", "--"):
            return {**base, "linestyle": "dashed", "dashes": (st.line_width, st.dash_spacing)}
        return {**base, "linestyle": spec}

    @staticmethod
    def _text_extents(fig, texts):
        """Measure the rendered extents of `texts`, in pixels, using the background box if any.

        matplotlib will not report a label's size until it has been drawn, so this must
        run after a draw.
        """
        if not texts:
            return []
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        return [(text.get_bbox_patch() or text).get_window_extent(renderer) for text in texts]

    def _text_height_points(self, fig, texts):
        """Height of the tallest of `texts`, in points. Zero if there are none."""
        extents = self._text_extents(fig, texts)
        if not extents:
            return 0.0
        return max(e.height for e in extents) * 72.0 / fig.dpi

    @staticmethod
    def _preferred_above(series_ys, i, neighbours=()):
        """Which side of its point a label sits on: outside its own bend, or into open space."""
        y = series_ys[i]
        at_an_end = len(series_ys) == 1 or i in (0, len(series_ys) - 1)

        # An end point has a slope but no bend, so curvature says nothing about it.
        # Use the open side: the outermost series at an x has nothing beyond it.
        if at_an_end:
            others = [other for other in neighbours if not np.isclose(other, y)]
            if others:
                if y > max(others):
                    return True
                if y < min(others):
                    return False

        if len(series_ys) == 1:
            return True
        if i == 0:
            return series_ys[1] < series_ys[0]  # curve heads down: the point is the high side
        if i == len(series_ys) - 1:
            return series_ys[-2] < series_ys[-1]  # curve arrives rising: the point is the high side
        curvature = series_ys[i + 1] - 2 * series_ys[i] + series_ys[i - 1]
        if curvature == 0:  # straight through: keep to the outside of the direction of travel
            return series_ys[i] > series_ys[i - 1]
        return curvature < 0  # concave down is a peak; concave up is a valley

    def _fit_axes_to_text(self, fig, ax, texts, pad, passes=6):
        """Grow the y-limits so every one of `texts` sits inside the axes, plus `pad`.

        Iterated: a label is a fixed size in points, so widening the limits makes it span
        *more* data units, not fewer. One pass undershoots.
        """
        if not texts:
            return
        for _ in range(passes):
            extents = self._text_extents(fig, texts)
            inverse = ax.transData.inverted()
            lows = [inverse.transform((e.x0, e.y0))[1] for e in extents]
            highs = [inverse.transform((e.x1, e.y1))[1] for e in extents]
            y_min, y_max = ax.get_ylim()
            fitted = (min(y_min, min(lows) - pad), max(y_max, max(highs) + pad))
            if fitted == (y_min, y_max):
                return
            ax.set_ylim(*fitted)

    def _legend_font(self, opts):
        """Font for the legend, consuming `prop` and `fontsize` from `opts`.

        `prop` overrides the plot font, as a dict of properties or a FontProperties.
        It is resolved here rather than forwarded because we pass `prop` ourselves to
        carry the font family, and matplotlib ignores `fontsize` whenever `prop` is set.
        """
        font = self.font_properties.copy()
        font.set_size(self.font_size)

        prop = opts.pop("prop", None)
        if isinstance(prop, FontProperties):
            font = prop.copy()
        elif isinstance(prop, dict):
            for key, value in prop.items():
                setter = getattr(font, f"set_{key}", None)
                if setter is None:
                    raise TypeError(f"Unknown font property '{key}' in legend prop")
                setter(value)
        elif prop is not None:
            raise TypeError(f"legend 'prop' must be a dict or FontProperties, got {type(prop).__name__}")

        if "fontsize" in opts:  # the shorthand wins, as it does in matplotlib
            font.set_size(opts.pop("fontsize"))
        return font

    @staticmethod
    def _x_positions(indices, x_values):
        """Map index positions onto real x values, if any were given.

        `indices` can be fractional, so this interpolates rather than looks up.
        """
        if x_values is None:
            return indices
        return list(np.interp(indices, np.arange(len(x_values)), x_values))

    @staticmethod
    def _validate_x(x, n_points):
        """Check `x` covers every index the energies use."""
        if x is None:
            return None
        try:
            x = [float(v) for v in x]
        except (TypeError, ValueError) as e:
            raise TypeError(f"'x' must be a sequence of numbers: {e}") from e
        if len(x) < n_points:
            raise ValueError(f"'x' has {len(x)} values but the longest series has {n_points} points.")
        return x

    def _series_curve(self, points, st):
        """Bezier through `points`, pulled back to the bar ends when drawing bars."""
        points = [(float(x), float(y)) for x, y in points]
        if st.point_type == "bar" and st.connect_bar_ends:
            half = st.bar_length / 2
            last = len(points) - 1
            adjusted = []
            for j, (x_pt, y_pt) in enumerate(points):
                if j == 0:
                    adjusted.append((x_pt + half, y_pt))
                elif j == last:
                    adjusted.append((x_pt - half, y_pt))
                else:
                    adjusted.append((x_pt - half, y_pt))
                    adjusted.append((x_pt + half, y_pt))
            points = adjusted

        segments = []
        for (x0, y0), (x1, y1) in pairwise(points):
            p0 = np.array([x0, y0])
            p1 = np.array([x0 + st.curviness * (x1 - x0), y0])
            p2 = np.array([x1 - st.curviness * (x1 - x0), y1])
            p3 = np.array([x1, y1])
            segments.append(cubic_bezier_points(p0, p1, p2, p3))
        return np.vstack(segments) if segments else None

    def _draw_points(self, ax, xs, ys, st, color):
        """Draw the markers for one series, in the point style of its axis."""
        for x_pt, y_pt in zip(xs, ys, strict=True):
            if np.isnan(y_pt):
                continue
            if st.point_type == "bar":
                ax.plot(
                    [x_pt - st.bar_length / 2, x_pt + st.bar_length / 2],
                    [y_pt, y_pt],
                    color="black",
                    lw=st.bar_width,
                )
            elif st.point_type in ("dot", "."):
                ax.plot(x_pt, y_pt, "o", markersize=st.marker_size, color=color)
            elif st.point_type in ("hollow", "o"):
                ax.plot(
                    x_pt,
                    y_pt,
                    marker="o",
                    markersize=st.marker_size,
                    markerfacecolor="white",
                    markeredgecolor=color,
                    markeredgewidth=st.line_width,
                )

    def _get_font_properties(self, font_dict):
        requested_family = font_dict.get("font_family", "sans-serif")

        available_fonts = {f.name for f in fontManager.ttflist}
        if requested_family not in available_fonts:
            logger.info(f"Font '{requested_family}' not found. Using fallback 'DejaVu Sans'.")
            requested_family = "DejaVu Sans"

        return FontProperties(
            family=requested_family,
            weight=font_dict.get("font_weight", "normal"),
            style=font_dict.get("font_style", "normal"),
            size=font_dict.get("font_size", 10),
        )

    def _resolve_colors(self, setting, num_colors):
        try:
            if isinstance(setting, str):
                try:
                    return sns.color_palette(setting, num_colors)
                except ValueError:
                    cmap = plt.get_cmap(setting)
                    return [cmap(i / num_colors) for i in range(num_colors)]

            elif isinstance(setting, list):
                if len(setting) < num_colors:
                    logger.warning(
                        f"Color list has only {len(setting)} colors but {num_colors} are needed. "
                        "Repeating colors, please adjust if required."
                    )
                    repeats = (num_colors + len(setting) - 1) // len(setting)
                    return (setting * repeats)[:num_colors]
                return setting[:num_colors]
            elif callable(setting):  # matplotlib colormap object
                return [setting(i / num_colors) for i in range(num_colors)]
            else:
                logger.error(
                    f"Invalid colour {setting}; `colors` must be a palette name (str), colormap object, "
                    "or list of color codes. Defaulting to 'viridis' cmap."
                )
        except Exception:
            logger.error("Error resolving colors: Check for typos. Defaulting to 'viridis' cmap.")
        fallback = plt.get_cmap("viridis")
        return [fallback(i / num_colors) for i in range(num_colors)]

    def _validate_energy_list(self, lst, label=None):
        if not isinstance(lst, list):
            raise TypeError(f"Energy profile '{label}' must be a list." if label else "Energy profile must be a list.")

        label_str = f" in '{label}'" if label else ""
        valid_list = []

        for i, val in enumerate(lst):
            if val is None:
                valid_list.append(None)
            elif isinstance(val, (int, float)):
                valid_list.append(float(val))
            elif isinstance(val, str):
                try:
                    valid_list.append(float(val))
                except ValueError as e:
                    raise ValueError(f"Could not convert string to float at index {i}{label_str}: '{val}'") from e
            else:
                raise TypeError(f"Invalid energy value at index {i}{label_str}: {val} (type {type(val)})")
        return valid_list

    def _draw_secondary(self, ax, secondary, exclude_from_legend, x=None):
        """Draw a second set of series on a right-hand y-axis.

        Drawn in the shared style, with anything in `y2` overriding it for this axis
        alone. Only the defaults differ: a separate palette, and dashed.
        """
        st = self._axis_style({"colors": "plasma", "linestyle": "--", **self.y2})
        ax2 = ax.twinx()
        labels = list(secondary.keys())
        colors = self._resolve_colors(st.colors, len(labels))
        light = [desaturate_colour(c, st.desaturate_factor) for c in colors] if st.desaturate else colors
        handles = []

        for i, label in enumerate(labels):
            values = [np.nan if v is None else float(v) for v in secondary[label]]
            xs, ys = generate_coordinates(values)
            if len(xs) < 2:
                logger.warning(f"Not enough points to draw secondary series '{label}'. Skipping.")
                continue
            xs = self._x_positions(xs, x)
            line = self._line_kwargs(st, label)
            curve = self._series_curve(list(zip(xs, ys, strict=True)), st)
            if curve is not None:
                ax2.plot(
                    curve[:, 0],
                    curve[:, 1],
                    color=light[i],
                    linewidth=st.line_width,
                    zorder=1,
                    **line,
                )
            self._draw_points(ax2, xs, ys, st, colors[i])
            handles.append(
                Line2D(
                    [0],
                    [0],
                    color=light[i],
                    linewidth=st.line_width,
                    linestyle=line["linestyle"],
                    label=label,
                    dash_capstyle="round",
                )
            )

        # The right-hand spine and ticks follow `axes` too.
        for spine in ax2.spines.values():
            spine.set_visible(False)
        if self.axes in ("y", "both", "box"):
            ax2.spines["right"].set_visible(True)
            ax2.spines["right"].set_linewidth(self.axis_linewidth)
            ax2.tick_params(axis="y", which="both", right=True, labelright=True)
            ax2.tick_params(axis="y", labelsize=self.font_size, width=self.axis_linewidth)
            if st.label:
                ax2.set_ylabel(st.label, fontproperties=self.font_properties)
        else:
            ax2.tick_params(axis="y", which="both", right=False, labelright=False)
            ax2.set_ylabel("")

        ax2.margins(y=0.15)
        return ax2, [h for h in handles if h.get_label() not in exclude_from_legend]

    def plot(
        self,
        energy_data,
        filename=None,
        annotations=None,
        point_labels=None,
        file_format="png",
        dpi=600,
        include_keys=None,
        exclude_from_legend=None,
        secondary=None,
        x=None,
    ):
        """Draw a profile from a dict of named series, a list of lists, or a single list.

        `x` gives the series a real reaction coordinate instead of the point index.
        Annotations are given in indices either way.

        Saves to `filename`.`file_format` if a filename is given. Returns None, so that
        Jupyter's inline backend does not display the figure twice.
        """
        exclude_from_legend = [] if exclude_from_legend is None else exclude_from_legend

        processed_dict = {}
        if isinstance(energy_data, dict):
            for label, values in energy_data.items():
                processed_dict[label] = self._validate_energy_list(values, label=label)
            logger.info("Using a valid dictionary of named energy profiles.")
        elif isinstance(energy_data, list):
            if all(isinstance(sublist, list) for sublist in energy_data):
                for i, sublist in enumerate(energy_data):
                    processed_dict[f"_unlabeled_{i}"] = self._validate_energy_list(sublist, label=f"list {i + 1}")
                logger.info("Using a valid list of lists with unnamed energy profiles.")
            else:
                processed_dict["_unlabeled_"] = self._validate_energy_list(energy_data)
                logger.info("Using a valid single list with one energy profile.")
        else:
            logger.error(f"Invalid input type for energy_data: {type(energy_data)}")
            raise TypeError("Data input must be a dict, list of lists, or a single list.")

        if annotations is not None:
            if not isinstance(annotations, dict):
                logger.warning("Annotations should be a dictionary of label: (start, end). Skipping annotations.")
                annotations = None
            else:
                clean_annotations = {}
                for label, val in annotations.items():
                    if (
                        isinstance(val, (tuple, list))
                        and len(val) == 2
                        and all(isinstance(v, (int, float)) for v in val)
                    ):
                        clean_annotations[label] = tuple(val)
                    else:
                        logger.warning(f"Invalid annotation '{label}': {val}. Skipping.")
                annotations = clean_annotations
        self.annotations = annotations

        if include_keys is not None:
            processed_dict = {k: v for k, v in processed_dict.items() if k in include_keys}
        labels = list(processed_dict.keys())
        energy_sets = [  # convert None to np.nan
            [e if e is not None else np.nan for e in processed_dict[k]] for k in labels
        ]

        n_points = max((len(v) for v in processed_dict.values()), default=0)
        if secondary:
            n_points = max(n_points, *(len(v) for v in secondary.values()))
        # Bound to its own name: `x` is reused as a loop variable all through this method.
        x_values = self._validate_x(x, n_points)

        if point_labels is not None:
            if isinstance(point_labels, dict):
                processed_point_labels = {}
                for label, values in point_labels.items():
                    if label in processed_dict:
                        if len(values) > len(processed_dict[label]):
                            logger.warning(
                                f"Point labels for '{label}' is longer than the energy profile length. Skipping."
                            )
                            continue
                        processed_point_labels[label] = [str(v) if v is not None else None for v in values]
            elif isinstance(point_labels, list):
                processed_point_labels = {}
                if all(isinstance(sublist, list) for sublist in point_labels):
                    for i, sublist in enumerate(cast("list[list[Any]]", point_labels)):
                        label = f"_unlabeled_{i}"
                        if label in processed_dict and len(sublist) == len(processed_dict[label]):
                            processed_point_labels[label] = [str(v) if v is not None else None for v in sublist]
                else:
                    label = "_unlabeled_"
                    if label in processed_dict and len(point_labels) == len(processed_dict[label]):
                        processed_point_labels[label] = [str(v) if v is not None else None for v in point_labels]
            else:
                logger.warning("point_labels must be a dict or list. Skipping point labels.")
                processed_point_labels = None
        else:
            processed_point_labels = None

        coords = [generate_coordinates(e) for e in energy_sets]
        coords = [(self._x_positions(xs, x_values), ys) for xs, ys in coords]
        all_energies = [e for xs, ys in coords for e in ys if not np.isnan(e)]
        if not all_energies:
            raise ValueError("No energies to plot: every series is empty or all None.")
        energy_span = max(all_energies) - min(all_energies)
        buffer_space = self.buffer_factor * energy_span  # how far a label sits off its point

        primary = self._axis_style(self.y1)

        colors = self._resolve_colors(primary.colors, len(energy_sets))
        colors = colors[::-1]

        light_colors = (
            [desaturate_colour(c, primary.desaturate_factor) for c in colors] if primary.desaturate else colors
        )

        fig, ax = plt.subplots(figsize=self.figsize)
        if self.labels:
            ax.margins(x=0.08, y=0.1)  # Add to avoid label overlap with edge of plot

        # --- draw curves
        for i, (xs, y) in enumerate(reversed(coords)):
            valid_points = [(xi, yi) for xi, yi in zip(xs, y, strict=True) if not np.isnan(yi)]
            if len(valid_points) < 2:
                logger.info(
                    f"Not enough valid points for curve - just plotting an individual point for series: {labels[i]}"
                )
                continue
            label = labels[len(coords) - 1 - i]
            line = self._line_kwargs(primary, label)

            all_points = self._series_curve(valid_points, primary)
            if all_points is None:
                logger.warning(f"No valid points to draw curve for label '{label}'. Skipping.")
                continue
            ax.plot(
                all_points[:, 0],
                all_points[:, 1],
                color=light_colors[i],
                linewidth=primary.line_width,
                **line,
            )
            if label not in exclude_from_legend:
                legend_line = Line2D(
                    [0],
                    [0],
                    color=light_colors[i],
                    linewidth=primary.line_width,
                    linestyle=line["linestyle"],
                    label=label,
                    dash_capstyle="round",
                )
                ax.add_line(legend_line)

        # --- draw points
        for i, (xs, y) in enumerate(reversed(coords)):
            self._draw_points(ax, xs, y, primary, colors[i])

        # --- draw points and labels
        label_texts = []
        if self.labels or processed_point_labels:
            labeled = []  # (x, y of the value label, above?, energy) per labelled point
            labeled_set = set()

            series_points = [
                [(px, py) for px, py in zip(xs_, ys_, strict=True) if not np.isnan(py)] for xs_, ys_ in coords
            ]

            # Every series' value at each x, so a point can tell if it is the outermost there
            at_x = {}
            for points in series_points:
                for px, py in points:
                    at_x.setdefault(round(px, 3), []).append(py)

            point_label_map = {}
            if processed_point_labels is not None:
                for i, (_x, y) in enumerate(reversed(coords)):
                    profile_label = labels[len(coords) - 1 - i]
                    if profile_label not in processed_point_labels:
                        continue

                    point_label_list = processed_point_labels[profile_label]
                    energy_profile = processed_dict[profile_label]

                    if len(point_label_list) < len(energy_profile):
                        point_label_list = point_label_list + [None] * (len(energy_profile) - len(point_label_list))

                    current_idx = 0
                    while current_idx < len(energy_profile):
                        if energy_profile[current_idx] is None:
                            current_idx += 1
                            continue

                        end_idx = current_idx + 1
                        while (
                            end_idx < len(energy_profile)
                            and energy_profile[end_idx] == energy_profile[current_idx]
                            and energy_profile[end_idx] is not None
                        ):
                            end_idx += 1

                        for energy in y:
                            if np.isclose(energy, energy_profile[current_idx], atol=1e-3):
                                for idx in range(current_idx, min(end_idx, len(point_label_list))):
                                    if point_label_list[idx] is not None:
                                        if end_idx - current_idx > 1:
                                            x_pos = (current_idx + end_idx - 1) / 2
                                        else:
                                            x_pos = current_idx
                                        point_label_map[(x_pos, energy)] = point_label_list[idx]
                                        break

                        current_idx = end_idx

            for points in series_points:
                series_ys = [py for _, py in points]
                for i, (x_pt, energy) in enumerate(points):
                    above = self._preferred_above(series_ys, i, at_x[round(x_pt, 3)])
                    preferred_y = energy + buffer_space if above else energy - buffer_space

                    # Typographic minus, not a hyphen: it renders at the same width as the digits.
                    label_text = f"{energy:.{self.sig_figs}f}".replace("-", "−")  # noqa: RUF001

                    value_text = None
                    if self.labels:
                        label_key = (round(x_pt, 3), label_text)
                        if label_key in labeled_set:
                            continue
                        labeled_set.add(label_key)
                        value_text = ax.text(
                            x_pt,
                            preferred_y,
                            label_text,
                            ha="center",
                            va="center",
                            fontproperties=self.font_properties,
                            fontweight="normal",
                        )
                        label_texts.append(value_text)

                    labeled.append((x_pt, preferred_y, above, energy))

            # The point label sits beyond the value label, offset in *points*: a text's
            # height in points is fixed, its height in data units is not.
            if processed_point_labels is not None:
                offset = self._text_height_points(fig, label_texts) / 2 + _LABEL_GAP_POINTS
                for x_pt, y, above, energy in labeled:
                    point_label = next(
                        (
                            text
                            for (px, py), text in point_label_map.items()
                            if abs(px - x_pt) < 1e-3 and abs(py - energy) < 1e-3
                        ),
                        None,
                    )
                    if point_label is None:
                        continue
                    label_texts.append(
                        ax.annotate(
                            point_label,
                            xy=(x_pt, y),
                            xytext=(0, offset if above else -offset),
                            textcoords="offset points",
                            ha="center",
                            va="bottom" if above else "top",
                            fontproperties=self.font_properties,
                            fontsize=self.font_size,
                            color=self.point_label_color,
                        )
                    )

            self._fit_axes_to_text(fig, ax, label_texts, buffer_space)

        # --- secondary y-axis
        secondary_handles = []
        if secondary:
            _, secondary_handles = self._draw_secondary(ax, secondary, exclude_from_legend, x_values)

        # --- legend
        if self.show_legend:
            handles, labels_ = [], []
            for handle, label in zip(*ax.get_legend_handles_labels(), strict=True):
                if label and not label.startswith("_unlabeled_"):
                    handles.append(handle)
                    labels_.append(label)
            handles, labels_ = handles[::-1], labels_[::-1]
            handles += secondary_handles
            labels_ += [h.get_label() for h in secondary_handles]
            if handles:
                opts = dict(self.legend)
                outside = bool(opts.pop("outside", False))
                anchor = opts.pop("anchor", 1.02)
                font = self._legend_font(opts)
                if outside:
                    # With bbox_to_anchor set, `loc` anchors *that corner* of the legend
                    # to the bbox point, so a right-hand loc extends the box back over the plot.
                    if "right" in str(opts.get("loc", "")):
                        logger.warning(
                            f"legend loc='{opts['loc']}' with outside=True anchors the legend's right "
                            f"edge beside the axes, so it will overlap the plot. Use a left-hand loc "
                            f"('center left', 'upper left'), or drop outside=True to place it inside."
                        )
                    opts.setdefault("loc", "center left")
                    opts.setdefault("bbox_to_anchor", (anchor, 0.5))
                # An outside legend sits beside the axes, where a frame just boxes
                # empty space; an inside one keeps matplotlib's frame.
                opts.setdefault("frameon", not outside)
                ax.legend(handles, labels_, prop=font, **opts)

        # --- segment annotations with double-headed arrows
        annotation_texts = []
        if self.annotations:
            y_min, _ = ax.get_ylim()
            y_arrow = y_min - self.annotation_buffer * energy_span  # place below data
            for label, span in self.annotations.items():
                # Annotations are given in indices, so they follow the data onto `x`.
                x_start, x_end = self._x_positions(list(span), x_values)
                ax.annotate(
                    "",
                    xy=(x_end, y_arrow),
                    xytext=(x_start, y_arrow),
                    arrowprops={
                        "arrowstyle": "<->",
                        "color": self.arrow_color,
                        "lw": self.arrow_width,
                        "shrinkA": 0.5,
                        "shrinkB": 0.5,
                    },
                    annotation_clip=False,
                )

                x_center = (x_start + x_end) / 2

                if not self.annotation_below_arrow:
                    # The white background breaks the arrow behind the text -- and paints
                    # over anything else it lands on, so the axes must grow to fit it.
                    bbox_props = {
                        "boxstyle": "round,pad=0.2",
                        "facecolor": "white",
                        "edgecolor": "none",
                    }
                    text = ax.annotate(
                        label,
                        xy=(x_center, y_arrow),
                        xytext=(0, 0),
                        textcoords="offset points",
                        ha="center",
                        va="center",
                        color=self.annotation_color,
                        bbox=bbox_props,
                        **self.annotation_kwargs,
                    )
                else:
                    text = ax.text(
                        x_center,
                        y_arrow - 0.3,
                        label,
                        ha="center",
                        va="top",
                        color=self.annotation_color,
                        **self.annotation_kwargs,
                    )
                annotation_texts.append(text)

        if primary.label is not None:
            ax.set_ylabel(primary.label, fontproperties=self.font_properties)
        else:
            if self.units.lower() == "kj":
                units = "kJ/mol"
            else:
                units = "kcal/mol"
            if self.energy.lower() == "e" or self.energy.lower() == "energy" or self.energy.lower() == "electronic":
                energy = "E"
            elif self.energy.lower() == "h" or self.energy.lower() == "enthalpy":
                energy = "H"
            elif self.energy.lower() == "s" or self.energy.lower() == "entropy":
                energy = "S"
            else:
                energy = "G"
            ax.set_ylabel(f"Δ{energy} ({units})", fontproperties=self.font_properties)
        if self.x_label is not None:
            ax.set_xlabel(self.x_label, fontproperties=self.font_properties)
        else:
            ax.set_xlabel("Reaction Coordinate", fontproperties=self.font_properties)

        for spine in ax.spines.values():
            spine.set_visible(False)

        if not self.x_indices:
            ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)

        ax.tick_params(axis="y", which="both", left=False, right=False, labelleft=False, labelright=False)

        if self.axes == "x":
            ax.spines["bottom"].set_visible(True)
            ax.spines["bottom"].set_linewidth(self.axis_linewidth)
            ax.set_ylabel("")

            if self.x_indices:
                ax.tick_params(
                    axis="x",
                    which="both",
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )

        elif self.axes == "y":
            ax.spines["left"].set_visible(True)
            ax.spines["left"].set_linewidth(self.axis_linewidth)
            ax.set_xlabel("")

            ax.tick_params(
                axis="y",
                which="both",
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )

        elif self.axes == "both":
            ax.spines["bottom"].set_visible(True)
            ax.spines["left"].set_visible(True)
            ax.spines["bottom"].set_linewidth(self.axis_linewidth)
            ax.spines["left"].set_linewidth(self.axis_linewidth)

            if self.x_indices:
                ax.tick_params(
                    axis="x",
                    which="both",
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )

            ax.tick_params(
                axis="y",
                which="both",
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )

        elif self.axes == "box":
            for spine_name in ["bottom", "top", "left", "right"]:
                ax.spines[spine_name].set_visible(True)
                ax.spines[spine_name].set_linewidth(self.axis_linewidth)

            if self.x_indices:
                ax.tick_params(
                    axis="x",
                    which="both",
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )

            ax.tick_params(
                axis="y",
                which="both",
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )

        else:
            ax.set_xlabel("")
            ax.set_ylabel("")

        if self.square:
            ax.set_box_aspect(1)

        fig.tight_layout()

        # tight_layout resizes the axes, so a label of fixed point size now spans a
        # different number of data units. Fit again, each group with its own pad.
        self._fit_axes_to_text(fig, ax, label_texts, buffer_space)
        self._fit_axes_to_text(fig, ax, annotation_texts, self.annotation_space * energy_span)

        if filename:
            fig.savefig(f"{filename}.{file_format}", format=file_format, dpi=dpi, bbox_inches="tight")


# Arguments of plot(); everything else is a style key.
_PLOT_ARGS = frozenset(inspect.signature(ReactionProfilePlotter.plot).parameters) - {"self", "energy_data"}


def plot_reaction_profile(energy_data, style="default", **kwargs):
    """Plot a profile in one call, splitting style keys from plot arguments."""
    plot_kwargs = {k: v for k, v in kwargs.items() if k in _PLOT_ARGS}
    style_kwargs = {k: v for k, v in kwargs.items() if k not in _PLOT_ARGS}
    plotter = ReactionProfilePlotter(style=style, **style_kwargs)
    return plotter.plot(energy_data, **plot_kwargs)

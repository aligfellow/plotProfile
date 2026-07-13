import matplotlib.pyplot as plt
import matplotlib.colors as mpc
from matplotlib.path import Path 
from matplotlib.lines import Line2D
import seaborn as sns
import numpy as np
from itertools import cycle
from matplotlib.patches import Circle
from matplotlib.transforms import Bbox
from matplotlib.font_manager import FontProperties, fontManager

import colorsys
import json
import importlib.resources as pkg_resources

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def _load_style(style_name):
    with pkg_resources.files('plotprofile').joinpath('styles.json').open('r') as f:
        styles = json.load(f)

    base = styles.get("default", {})
    overlay = styles.get(style_name, {})
    base.update(overlay)
    return base

def desaturate_colour(color, factor=1.2):
    rgb = mpc.to_rgb(color)
    hls = colorsys.rgb_to_hls(*rgb)
    hls_new = (hls[0], 1 - (0.4 * factor), 0.3 * factor)
    return colorsys.hls_to_rgb(*hls_new)


def generate_coordinates(energies):
    x_coords, y_coords = [], []
    i = 0
    while i < len(energies):
        if energies[i] is None:
            i += 1
            continue
            
        # Start tracking a new segment
        start_idx = i
        current_energy = energies[i]
        
        # Find end of consecutive non-None duplicates
        j = i + 1
        while j < len(energies) and energies[j] == current_energy and energies[j] is not None:
            j += 1
            
        # Calculate midpoint if we have consecutive duplicates
        if j - start_idx > 1:
            midpoint = (start_idx + j - 1) / 2
            x_coords.append(midpoint)
            y_coords.append(current_energy)
        else:
            x_coords.append(i)
            y_coords.append(current_energy)
            
        i = j
    return x_coords, y_coords

def cubic_bezier_points(P0, P1, P2, P3, num=500):
    t = np.linspace(0, 1, num)
    points = ((1 - t)**3)[:, None] * P0 + \
            3 * ((1 - t)**2)[:, None] * t[:, None] * P1 + \
            3 * (1 - t)[:, None] * (t**2)[:, None] * P2 + \
            (t**3)[:, None] * P3
    return points

class ReactionProfilePlotter:
    def __init__(self, style='default', **kwargs):
        try:
            style_dict = _load_style(style)
            if not style_dict:
                logger.warning(f"Style '{style}' not found. Using default style.")
                style_dict = _load_style('default')
        except Exception as e:
            logger.warning(f"Error loading style '{style}': {e}. Using default style.")
            style_dict = _load_style('default')
        style_dict.update(kwargs)

        try:
            self.figsize = tuple(style_dict.get('figsize', (5,4.5)))
            self.point_type = style_dict.get('point_type', 'dot')
            self.curviness = float(style_dict.get('curviness', 0.42))
            self.desaturate = bool(style_dict.get('desaturate', True))
            self.desaturate_factor = float(style_dict.get('desaturate_factor', 1.2))
            self.dashed = style_dict.get("dashed", [])
            if not isinstance(self.dashed, list):
                logger.warning("Expected 'dashed' to be a list of labels. Resetting to empty list.")
                self.dashed = []
            self.labels = bool(style_dict.get('labels', True))
            self.show_legend = bool(style_dict.get('show_legend', True))
            self.line_width = float(style_dict.get('line_width', 2))
            self.bar_width = float(style_dict.get('bar_width', 3))
            self.bar_length = float(style_dict.get('bar_length', 0.3))
            self.marker_size = float(style_dict.get('marker_size', 5))
            self.font_size = int(style_dict.get('font_size', 10))
            self.axes = style_dict.get('axes', '')
            self.axis_linewidth = float(style_dict.get('axis_linewidth', 1))
            self.colors = style_dict.get('colors', 'viridis')
            self.arrow_color = style_dict.get('arrow_color', 'black')
            self.annotation_color = style_dict.get('annotation_color', 'black')
            self.buffer_factor = float(style_dict.get('buffer_factor', 0.025))
            self.energy = style_dict.get('energy', 'G')
            self.units = style_dict.get('units', 'kcal')
            self.annotation_space = float(style_dict.get('annotation_space', 0.01))
            self.arrow_width = float(style_dict.get('arrow_width', 1.5))
            self.annotation_buffer = float(style_dict.get('annotation_buffer', 0.0))
            self.sig_figs = int(style_dict.get('sig_figs', 1))
            self.point_label_color = style_dict.get('point_label_color', 'black')
            self.annotation_below_arrow = bool(style_dict.get('annotation_below_arrow', False))
            self.connect_bar_ends = bool(style_dict.get('connect_bar_ends', True))
            self.dash_spacing = float(style_dict.get('dash_spacing', 2.5))
            self.x_label = style_dict.get('x_label', None)
            self.y_label = style_dict.get('y_label', None)
            self.x_indices = bool(style_dict.get('x_indices', False))
            # 'best' can land on top of the data when there are many series.
            self.legend_loc = style_dict.get('legend_loc', 'best')
            self.legend_outside = bool(style_dict.get('legend_outside', False))
            # How far right of the axes the outside legend sits. Needs to clear a
            # secondary axis and its label, if there is one.
            self.legend_anchor = float(style_dict.get('legend_anchor', 1.02))
            # Keep the *axes* square, whatever the figure has to be to fit a
            # legend beside it. Without this, moving the legend out squashes the
            # plot into a rectangle.
            self.square = bool(style_dict.get('square', False))
            self.y2_label = style_dict.get('y2_label', None)
            self.y2_colors = style_dict.get('y2_colors', 'plasma')
        except Exception as e:
            logger.error(f"Invalid style parameters: {e}")
            raise ValueError(f"Invalid style parameters: {e}")

        self.font_kwargs = {
            'fontsize': style_dict.get('font_size', 10),
        }
        self.font_properties = self._get_font_properties(style_dict)
        font_family = self.font_properties.get_family()
        font_family = font_family[0] if font_family else 'sans-serif'
        self.annotation_kwargs = {
            'fontsize': style_dict.get('annotation_size', self.font_size),
            'fontfamily': font_family,
            'fontweight': style_dict.get('annotation_weight', 'semibold'),
            'fontstyle': style_dict.get('annotation_style', 'italic'),
        }
    def _get_font_properties(self, font_dict):
        requested_family = font_dict.get('font_family', 'sans-serif')
        
        # Check if requested font is available
        available_fonts = {f.name for f in fontManager.ttflist}
        if requested_family not in available_fonts:
            logger.info(f"Font '{requested_family}' not found. Using fallback 'DejaVu Sans'.")
            requested_family = 'DejaVu Sans'

        return FontProperties(
            family=requested_family,
            weight=font_dict.get('font_weight', 'normal'),
            style=font_dict.get('font_style', 'normal'),
            size=font_dict.get('font_size', 10),
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
                    logger.warning(f"Color list has only {len(setting)} colors but {num_colors} are needed. Repeating colors, please adjust if required.")
                    repeats = (num_colors + len(setting) - 1) // len(setting)
                    return (setting * repeats)[:num_colors]
                return setting[:num_colors]
            elif hasattr(setting, "__call__"):  # matplotlib colormap object
                return [setting(i / num_colors) for i in range(num_colors)]
            else:
                logger.error(f"Invalid colour {setting}; `colors` must be a palette name (str), colormap object, or list of color codes. Defaulting to 'viridis' cmap.")
        except Exception as e:
            logger.error(f"Error resolving colors: Check for typos. Defaulting to 'viridis' cmap.")
            fallback = plt.get_cmap('viridis')
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
                except ValueError:
                    raise ValueError(f"Could not convert string to float at index {i}{label_str}: '{val}'")
            else:
                raise TypeError(f"Invalid energy value at index {i}{label_str}: {val} (type {type(val)})")
        return valid_list

    def _curve(self, points):
        """Join points with a bezier of the configured curviness.

        curviness=0 puts both control points on the segment endpoints, which makes
        the curve exactly the straight line -- so a scan can be joined honestly,
        without inventing points that were never computed, using the same code path
        as a schematic profile.
        """
        points = [(float(x), float(y)) for x, y in points]
        segments = []
        for (x0, y0), (x1, y1) in zip(points[:-1], points[1:]):
            P0 = np.array([x0, y0])
            P1 = np.array([x0 + self.curviness * (x1 - x0), y0])
            P2 = np.array([x1 - self.curviness * (x1 - x0), y1])
            P3 = np.array([x1, y1])
            segments.append(cubic_bezier_points(P0, P1, P2, P3))
        return np.vstack(segments)

    def _draw_secondary(self, ax, secondary, exclude_from_legend):
        """Draw a second set of series on a right-hand y-axis.

        For quantities that share the reaction coordinate but not the unit -- bond
        lengths against energy, say. Two scales on one plot are easy to misread, so
        this is opt-in and the axis is always labelled.
        """
        ax2 = ax.twinx()
        labels = list(secondary.keys())
        colors = self._resolve_colors(self.y2_colors, len(labels))
        handles = []

        for i, label in enumerate(labels):
            values = [np.nan if v is None else float(v) for v in secondary[label]]
            xs, ys = generate_coordinates(values)
            if len(xs) < 2:
                logger.warning(f"Not enough points to draw secondary series '{label}'. Skipping.")
                continue
            curve = self._curve(list(zip(xs, ys)))
            ax2.plot(curve[:, 0], curve[:, 1], color=colors[i], linewidth=self.line_width,
                     linestyle='dashed', dashes=(self.line_width, self.dash_spacing),
                     dash_capstyle='round', zorder=1)
            ax2.plot(xs, ys, 'o', color=colors[i], markersize=self.marker_size,
                     markerfacecolor='white', markeredgewidth=self.line_width * 0.6, zorder=2)
            handles.append(Line2D([0], [0], color=colors[i], linewidth=self.line_width,
                                  linestyle='dashed', label=label, dash_capstyle='round'))

        if self.y2_label:
            ax2.set_ylabel(self.y2_label, fontproperties=self.font_properties)
        ax2.tick_params(axis='y', labelsize=self.font_size, width=self.axis_linewidth)
        ax2.margins(y=0.15)
        return ax2, [h for h in handles if h.get_label() not in exclude_from_legend]

    def plot(self, energy_data, filename=None, annotations=None, point_labels=None, file_format='png', dpi=600, include_keys=None, exclude_from_legend=[], secondary=None):

        processed_dict = {}
        if isinstance(energy_data, dict):
            # Dict of named profiles: {label: [values]}
            for label, values in energy_data.items():
                processed_dict[label] = self._validate_energy_list(values, label=label)
            logger.info("Using a valid dictionary of named energy profiles.")
        elif isinstance(energy_data, list):
            if all(isinstance(sublist, list) for sublist in energy_data):
                # List of lists
                for i, sublist in enumerate(energy_data):
                    processed_dict[f"_unlabeled_{i}"] = self._validate_energy_list(sublist, label=f"list {i+1}")
                logger.info("Using a valid list of lists with unnamed energy profiles.")
            else:
                # Single list
                processed_dict[f"_unlabeled_"] = self._validate_energy_list(energy_data)
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
                    if (isinstance(val, (tuple, list)) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val)):
                        clean_annotations[label] = tuple(val)
                    else:
                        logger.warning(f"Invalid annotation '{label}': {val}. Skipping.")
                annotations = clean_annotations
        self.annotations = annotations

        if include_keys is not None:
            processed_dict = {k: v for k, v in processed_dict.items() if k in include_keys}
        labels = list(processed_dict.keys())
        energy_sets = [  # convert None to np.nan
            [e if e is not None else np.nan for e in processed_dict[k]]
            for k in labels
        ]
        dashed_indices = [labels.index(k) for k in self.dashed if k in labels]

        # Process point labels if provided
        if point_labels is not None:
            if isinstance(point_labels, dict):
                # Convert dict format to match processed_dict keys
                processed_point_labels = {}
                for label, values in point_labels.items():
                    if label in processed_dict:
                        # Validate length matches energy profile
                        if len(values) > len(processed_dict[label]):
                            logger.warning(f"Point labels for '{label}' is longer than the energy profile length. Skipping.")
                            continue
                        processed_point_labels[label] = [
                            str(v) if v is not None else None for v in values
                        ]
            elif isinstance(point_labels, list):
                # Convert list format to match processed_dict structure
                processed_point_labels = {}
                if all(isinstance(sublist, list) for sublist in point_labels):
                    # List of lists
                    for i, sublist in enumerate(point_labels):
                        label = f"_unlabeled_{i}"
                        if label in processed_dict and len(sublist) == len(processed_dict[label]):
                            processed_point_labels[label] = [
                                str(v) if v is not None else None for v in sublist
                            ]
                else:
                    # Single list
                    label = "_unlabeled_"
                    if label in processed_dict and len(point_labels) == len(processed_dict[label]):
                        processed_point_labels[label] = [
                            str(v) if v is not None else None for v in point_labels
                        ]
            else:
                logger.warning("point_labels must be a dict or list. Skipping point labels.")
                processed_point_labels = None
        else:
            processed_point_labels = None

        coords = [generate_coordinates(e) for e in energy_sets]
        all_energies = [e for xs, ys in coords for e in ys if not np.isnan(e)]
        buffer_space = self.buffer_factor * (max(all_energies) - min(all_energies))
        buffer_range = 1.0

        base_colors = self.colors
        colors = self._resolve_colors(base_colors, len(energy_sets))
        colors = colors[::-1]

        light_colors = [desaturate_colour(c, self.desaturate_factor) for c in colors] if self.desaturate else colors

        fig, ax = plt.subplots(figsize=self.figsize)
        labeled_coords = set()
        if self.labels:
            ax.margins(x=0.08, y=0.1)  # Add to avoid label overlap with edge of plot

        # --- draw curves
        for i, (x, y) in enumerate(reversed(coords)):
            valid_points = [(xi, yi) for xi, yi in zip(x, y) if not np.isnan(yi)]
            if len(valid_points) < 2:
                # Not enough points to draw a line so skip and just draw a point
                logger.info(f"Not enough valid points for curve - just plotting an individual point for series: {labels[i]}")
                continue
            linestyle = 'dashed' if i in [len(coords) - 1 - d for d in dashed_indices] else 'solid'
            verts, codes = [], [Path.MOVETO]
            bar_adjust = self.point_type == 'bar' and self.connect_bar_ends
            bar_half_width = self.bar_length / 2

            processed_points = []
            for j, (x_pt, y_pt) in enumerate(valid_points):
                if bar_adjust:
                    if j == 0:
                        processed_points.append((x_pt + bar_half_width, y_pt))
                    elif j == len(valid_points) - 1:
                        processed_points.append((x_pt - bar_half_width, y_pt))
                    else:
                        processed_points.append((x_pt - bar_half_width, y_pt))
                        processed_points.append((x_pt + bar_half_width, y_pt))
                else:
                    processed_points.append((x_pt, y_pt))

            for j in range(0, len(processed_points) - 1):
                x0, y0 = processed_points[j]
                x1, y1 = processed_points[j + 1]

                if not verts:
                    verts.append([x0, y0])
                verts.append([x0 + self.curviness * (x1 - x0), y0])
                verts.append([x1 - self.curviness * (x1 - x0), y1])
                verts.append([x1, y1])
                codes += [Path.CURVE4, Path.CURVE4, Path.CURVE4]

            path = Path(verts, codes)
            label = labels[len(coords) - 1 - i]

            verts = np.array(verts)
            all_points = []
            for j in range(0, len(verts) - 3, 3):
                P0 = verts[j]
                P1 = verts[j + 1]
                P2 = verts[j + 2]
                P3 = verts[j + 3]
                bezier_points = cubic_bezier_points(P0, P1, P2, P3)
                all_points.append(bezier_points)
            if len(all_points) == 0:
                logger.warning(f"No valid points to draw curve for label '{label}'. Skipping.")
                continue
            all_points = np.vstack(all_points)
            ax.plot(all_points[:, 0], all_points[:, 1], color=light_colors[i], linewidth=self.line_width, dashes=(self.line_width,self.dash_spacing) if linestyle == 'dashed' else (self.line_width,0), linestyle=linestyle, dash_capstyle='round')
            if label not in exclude_from_legend:
                legend_line = Line2D(
                    [0], [0],
                    color=light_colors[i],
                    linewidth=self.line_width,
                    linestyle=linestyle,
                    label=label,
                    # dashes= (self.line_width, self.dash_spacing) if linestyle == 'dashed' else (self.line_width, 0),
                    dash_capstyle='round'
                )
                ax.add_line(legend_line)

        # --- draw points
        for i, (x, y) in enumerate(reversed(coords)):
            for j, energy in enumerate(y):
                if np.isnan(energy):
                    continue
                if self.point_type == 'bar':
                    ax.plot([x[j] - self.bar_length/2, x[j] + self.bar_length/2], [energy, energy], color='black', lw=self.bar_width)
                elif self.point_type in ['dot', '.']:
                    ax.plot(x[j], energy, 'o', markersize=self.marker_size, color=colors[i])
                elif self.point_type in ['hollow', 'o']:
                    ax.plot(x[j], energy, marker='o', markerfacecolor='white', markeredgecolor=colors[i], markeredgewidth=self.line_width)

        # --- draw points and labels
        if self.labels:
            label_coords = []
            label_vals = []
            labeled_set = set()
            curves = []
            texts = []

            label_extents = []
            point_label_extents = []

            # Sort points for local max detection
            sorted_points = sorted([(x, y) for coords_ in coords for x, y in zip(*coords_) if not np.isnan(y)], key=lambda p: p[0])
            x_group = {}
            for px, py in sorted_points:
                x_group.setdefault(round(px, 3), []).append(py)

            sorted_xs = sorted(set(round(px, 3) for px, _ in sorted_points))
            x_index_map = {xv: i for i, xv in enumerate(sorted_xs)}

            # Create a mapping from (x, energy) to point labels
            point_label_map = {}
            if processed_point_labels is not None:
                for i, (x, y) in enumerate(reversed(coords)):
                    profile_label = labels[len(coords) - 1 - i]
                    if profile_label not in processed_point_labels:
                        continue
                        
                    point_label_list = processed_point_labels[profile_label]
                    energy_profile = processed_dict[profile_label]
                    
                    # Pad point_labels with None if shorter than energy list
                    if len(point_label_list) < len(energy_profile):
                        point_label_list = point_label_list + [None] * (len(energy_profile) - len(point_label_list))
                    
                    # Track original indices accounting for consecutive duplicates
                    current_idx = 0
                    while current_idx < len(energy_profile):
                        if energy_profile[current_idx] is None:
                            current_idx += 1
                            continue
                            
                        # Find end of consecutive duplicates
                        end_idx = current_idx + 1
                        while (end_idx < len(energy_profile) and 
                            energy_profile[end_idx] == energy_profile[current_idx] and 
                            energy_profile[end_idx] is not None):
                            end_idx += 1
                        
                        # Check if this point exists in our coordinates
                        for j, (x_coord, energy) in enumerate(zip(x, y)):
                            if np.isclose(energy, energy_profile[current_idx], atol=1e-3):
                                # Get the label if it exists in the original profile
                                for idx in range(current_idx, min(end_idx, len(point_label_list))):
                                    if point_label_list[idx] is not None:
                                        # Calculate x position - midpoint if multiple points
                                        if end_idx - current_idx > 1:
                                            x_pos = (current_idx + end_idx - 1) / 2
                                        else:
                                            x_pos = current_idx
                                        point_label_map[(x_pos, energy)] = point_label_list[idx]
                                        break
                        
                        current_idx = end_idx

            for x, energy in sorted_points:
                rx = round(x, 3)
                idx = x_index_map.get(rx, None)

                is_local_max = False
                if idx is not None and 0 < idx < len(sorted_xs) - 1:
                    prev_x = sorted_xs[idx - 1]
                    next_x = sorted_xs[idx + 1]
                    current_y = max(x_group[rx])
                    prev_y = max(x_group[prev_x])
                    next_y = max(x_group[next_x])
                    is_local_max = current_y > prev_y and current_y > next_y

                preferred_above = is_local_max
                preferred_y = energy + buffer_space if preferred_above else energy - buffer_space

                def find_parent_curve_index(x, y, coords):
                    for i, (xs, ys) in enumerate(coords):
                        for x0, y0 in zip(xs, ys):
                            if np.isclose(x, x0, atol=1e-5) and np.isclose(y, y0, atol=1e-3):
                                return i
                    return None

                # Find which curve this point belongs to
                parent_idx = find_parent_curve_index(x, energy, coords)
                if parent_idx is None:
                    continue

                # Get y-values from other curves at this x
                other_yvals = []
                for i, (xs, ys) in enumerate(coords):
                    if i == parent_idx:
                        continue
                    # Interpolate y at x
                    try:
                        y_interp = np.interp(x, xs, ys)
                        other_yvals.append(y_interp)
                    except Exception:
                        continue

                if other_yvals:
                    nearest_other_y = min(other_yvals, key=lambda y: abs(preferred_y - y))
                    dist_to_own_curve = abs(preferred_y - energy)
                    dist_to_other_curve = abs(preferred_y - nearest_other_y)

                    if dist_to_other_curve < dist_to_own_curve:
                        # Label is nearer another curve — flip placement
                        preferred_above = not preferred_above
                        preferred_y = energy + buffer_space if preferred_above else energy - buffer_space

                # Proceed with energy label
                label_text = f"{energy:.{self.sig_figs}f}".replace('-', '−')
                label_key = (x, label_text)
                if label_key in labeled_set:
                    continue
                labeled_set.add(label_key)

                label_coords.append((x, preferred_y))
                label_vals.append(label_text)

                energy_label = ax.annotate(
                    label_text,
                    xy=(x, preferred_y),
                    xytext=(0, 0),
                    textcoords='offset points',
                    ha='center',
                    va='center',
                    fontproperties=self.font_properties,
                    fontweight='normal',
                )

                label_extents.append((x, preferred_y))

                # Add point label if it exists for this coordinate
                if processed_point_labels is not None:
                    # Find matching point label (accounting for floating point precision)
                    point_label = None
                    for (px, py), plabel in point_label_map.items():
                        if np.isclose(px, x, atol=1e-3) and np.isclose(py, energy, atol=1e-3):
                            point_label = plabel
                            break
                    
                    if point_label:
                        y_label = preferred_y + buffer_space if preferred_above else preferred_y - buffer_space
                        
                        ax.annotate(
                            point_label,
                            xy=(x, y_label),
                            xytext=(0, 0),
                            textcoords='offset points',
                            ha='center',
                            va='center',
                            fontproperties=self.font_properties,
                            fontsize=self.font_size,
                            color=self.point_label_color,
                        )
                        point_label_extents.append((x, y_label))
                        

            if label_extents or point_label_extents:
                all_y = [y for x, y in label_extents + point_label_extents] + all_energies
                y_min, y_max = min(all_y), max(all_y)
                
                # Add buffer space (using max of buffer_space or 10% of range)
                y_range = y_max - y_min
                padding = 2 * buffer_space
                ax.set_ylim(y_min - padding, y_max + padding)

        # --- secondary y-axis
        secondary_handles = []
        if secondary:
            _, secondary_handles = self._draw_secondary(ax, secondary, exclude_from_legend)

        # --- legend
        if self.show_legend:
            handles, labels_ = [], []
            for handle, label in zip(*ax.get_legend_handles_labels()):
                if label and not label.startswith('_unlabeled_'):
                    handles.append(handle)
                    labels_.append(label)
            handles, labels_ = handles[::-1], labels_[::-1]
            # Series on the right-hand axis belong in the same legend as those on
            # the left, or the reader cannot tell which scale a line is read against.
            handles += secondary_handles
            labels_ += [h.get_label() for h in secondary_handles]
            if handles:
                if self.legend_outside:
                    ax.legend(handles, labels_, loc='center left',
                              bbox_to_anchor=(self.legend_anchor, 0.5),
                              frameon=False, prop=self.font_properties)
                else:
                    ax.legend(handles, labels_, loc=self.legend_loc, prop=self.font_properties)

        # --- segment annotations with double-headed arrows
        if self.annotations:
            y_min, _ = ax.get_ylim()
            y_arrow = y_min - self.annotation_buffer * (max(all_energies) - min(all_energies))  # place below data
            increase_label_space = False
            for label, (x_start, x_end) in self.annotations.items():
                if "\n" in label:
                    increase_label_space = True # sort spacing automatically for labels with multiple lines
                # Draw double-headed arrow
                ax.annotate(
                    '', 
                    xy=(x_end, y_arrow), 
                    xytext=(x_start, y_arrow),
                    arrowprops=dict(
                        arrowstyle='<->',
                        color=self.arrow_color,
                        lw=self.arrow_width,
                        # ls='--',
                        shrinkA=0.5,
                        shrinkB=0.5,
                    ),
                    annotation_clip=False
                )

                x_center = (x_start + x_end) / 2
                
                if not self.annotation_below_arrow:
                    bbox_props = dict(
                    boxstyle='round,pad=0.2',
                    facecolor='white',
                    edgecolor='none',
                    ) 
                    ax.annotate(
                        label,
                        xy=(x_center, y_arrow),
                        xytext=(0, 0),
                        textcoords='offset points',
                        ha='center',
                        va='center',
                        color=self.annotation_color,
                        bbox=bbox_props,
                        **self.annotation_kwargs,
                    )
                else:
                    ax.text(
                        x_center, y_arrow - 0.3,
                        label,
                        ha='center', va='top',
                        color=self.annotation_color,
                        **self.annotation_kwargs,
                    )
            # only draw if there is no x-axis to be shown
            if self.axes in ['x', 'both', 'box']:
                y_min, y_max = ax.get_ylim()
                energy_range = max(all_energies) - min(all_energies)

                y_buffer = self.annotation_space * energy_range
                if increase_label_space:
                    y_buffer = y_buffer * 1.75
                if self.annotation_below_arrow:
                    y_buffer = y_buffer * 2
                ax.set_ylim(y_min - y_buffer, y_max)
            else:
                y_min, y_max = ax.get_ylim()
                energy_range = max(all_energies) - min(all_energies)

                y_buffer = self.annotation_space * energy_range 
                ax.set_ylim(y_min - y_buffer, y_max)

        if self.y_label is not None:
            ax.set_ylabel(self.y_label, fontproperties=self.font_properties)
        else:
            if self.units.lower() == "kj":
                units = 'kJ/mol'
            else:
                units = 'kcal/mol'
            if self.energy.lower() == 'e' or self.energy.lower() == 'energy' or self.energy.lower() == 'electronic':
                energy = 'E'
            elif self.energy.lower() == 'h' or self.energy.lower() == 'enthalpy': 
                energy = 'H'
            elif self.energy.lower() == 's' or self.energy.lower() == 'entropy':
                energy = 'S'
            else:
                energy = 'G'
            ax.set_ylabel(f'Δ{energy} ({units})', fontproperties=self.font_properties)
        if self.x_label is not None:
            ax.set_xlabel(self.x_label, fontproperties=self.font_properties)
        else:
            ax.set_xlabel('Reaction Coordinate', fontproperties=self.font_properties)

        # Hide all spines and ticks by default
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Remove all ticks and tick labels by default
        # Only hide x-axis if x_indices is False
        if not self.x_indices:
            ax.tick_params(
                axis='x', which='both',
                bottom=False, top=False,
                labelbottom=False
            )
        
        ax.tick_params(
            axis='y', which='both',
            left=False, right=False,
            labelleft=False, labelright=False
        )

        if self.axes == 'x':
            ax.spines['bottom'].set_visible(True)
            ax.spines['bottom'].set_linewidth(self.axis_linewidth)
            ax.set_ylabel(None)
            
            if self.x_indices:
                ax.tick_params(
                    axis='x', which='both',
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )

        elif self.axes == 'y':
            ax.spines['left'].set_visible(True)
            ax.spines['left'].set_linewidth(self.axis_linewidth)
            ax.set_xlabel(None)

            ax.tick_params(
                axis='y', which='both',
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )

            
        elif self.axes == 'both':
            ax.spines['bottom'].set_visible(True)
            ax.spines['left'].set_visible(True)
            ax.spines['bottom'].set_linewidth(self.axis_linewidth)
            ax.spines['left'].set_linewidth(self.axis_linewidth)

            if self.x_indices:
                ax.tick_params(
                    axis='x', which='both',
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )
            
            ax.tick_params(
                axis='y', which='both',
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )            


        elif self.axes == 'box':
            for spine_name in ['bottom', 'top', 'left', 'right']:
                ax.spines[spine_name].set_visible(True)
                ax.spines[spine_name].set_linewidth(self.axis_linewidth)

            if self.x_indices:
                ax.tick_params(
                    axis='x', which='both',
                    bottom=True,
                    labelbottom=True,
                    width=self.line_width,
                    length=5,
                    labelsize=self.font_size,
                )
            
            ax.tick_params(
                axis='y', which='both',
                left=True,
                labelleft=True,
                width=self.line_width,
                length=5,
                labelsize=self.font_size,
            )


        else:
            ax.set_xlabel(None)
            ax.set_ylabel(None)

        if self.square:
            ax.set_box_aspect(1)

        fig.tight_layout()

        if filename:
            fig.savefig(f"{filename}.{file_format}", format=file_format, dpi=dpi, bbox_inches='tight')

        return None


# Convenience function (no need to instantiate class)
def plot_reaction_profile(energy_data, **kwargs):
    plotter = ReactionProfilePlotter()
    return plotter.plot(energy_data, **kwargs)

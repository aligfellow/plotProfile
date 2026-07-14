import matplotlib.pyplot as plt
import numpy as np
import pytest

from plotprofile import ReactionProfilePlotter, plot_reaction_profile
from plotprofile.plot import generate_coordinates

ENERGIES = {
    "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5],
    "Pathway B": [None, -2.0, 6.2, 4.3],
}
ANNOTATIONS = {"Step 1": (0, 2), "Step 2": (2, 4)}


def test_x_positions_handle_gaps_and_repeats():
    # A None leaves a gap rather than shifting later points left...
    assert generate_coordinates([None, 5.0, 1.0]) == ([1, 2], [5.0, 1.0])
    # ...and a repeated value is drawn once, centred between its indices.
    assert generate_coordinates([0.0, 5.0, 5.0]) == ([0, 1.5], [0.0, 5.0])


def test_curviness_zero_is_a_straight_line():
    # curviness=0 must collapse the bezier onto the straight segment.
    plotter = ReactionProfilePlotter(curviness=0.0)
    curve = plotter._series_curve([(0.0, 0.0), (1.0, 1.0)], plotter._axis_style())
    assert np.allclose(curve[:, 0], curve[:, 1])


@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"style": "presentation", "point_type": "dot"},
        {"style": "straight", "point_type": "bar", "axes": "y"},
        {"colors": "Blues_r", "desaturate": False, "axes": "None"},
        {"linestyle": {"Pathway A": "--"}, "units": "kj", "energy": "electronic", "x_indices": True},
    ],
)
def test_renders_across_styles(tmp_path, kwargs):
    out = tmp_path / "p"
    ReactionProfilePlotter(**kwargs).plot(ENERGIES, annotations=ANNOTATIONS, filename=str(out), dpi=72)
    assert out.with_suffix(".png").stat().st_size > 0


@pytest.mark.parametrize("data", [ENERGIES, [0.0, 5.0, 5.0, -2.0], [[0.0, 10.0, 2.0], [None, 8.0, 1.0]]])
def test_accepts_each_input_shape(tmp_path, data):
    out = tmp_path / "p"
    ReactionProfilePlotter().plot(data, filename=str(out), dpi=72)
    assert out.with_suffix(".png").stat().st_size > 0


def test_saves_in_the_requested_format(tmp_path):
    out = tmp_path / "p"
    result = ReactionProfilePlotter().plot(ENERGIES, filename=str(out), file_format="svg", dpi=72)
    assert out.with_suffix(".svg").stat().st_size > 0
    # None, deliberately: returning the figure makes Jupyter show it twice.
    assert result is None


def test_secondary_axis_draws_extra_series(tmp_path):
    plain, with_y2 = tmp_path / "plain", tmp_path / "with_y2"
    plotter = ReactionProfilePlotter(y2={"label": "bond length (Å)"})
    plotter.plot(ENERGIES, filename=str(plain), dpi=72)
    plotter.plot(ENERGIES, secondary={"C-O": [1.4, 1.6, 2.1, 2.9]}, filename=str(with_y2), dpi=72)
    assert with_y2.with_suffix(".png").read_bytes() != plain.with_suffix(".png").read_bytes()


def test_y2_overrides_only_the_secondary_axis(tmp_path):
    inherited, overridden = tmp_path / "a", tmp_path / "b"
    secondary = {"C-O": [1.4, 1.6, 2.1, 2.9]}
    ReactionProfilePlotter(point_type="bar", curviness=0.0).plot(
        ENERGIES, secondary=secondary, filename=str(inherited), dpi=72
    )
    ReactionProfilePlotter(
        point_type="bar", curviness=0.0, y2={"point_type": "dot", "curviness": 0.42, "linestyle": "solid"}
    ).plot(ENERGIES, secondary=secondary, filename=str(overridden), dpi=72)
    assert overridden.with_suffix(".png").read_bytes() != inherited.with_suffix(".png").read_bytes()


def test_y1_and_y2_resolve_identically():
    # The two axes are the same config layer: same keys, same meanings. Only their
    # defaults differ (y2 gets its own palette, and dashes, to read as a second scale).
    overrides = {"curviness": 0.3, "point_type": "dot", "colors": "viridis", "line_width": 4.0}
    plotter = ReactionProfilePlotter(curviness=0.0, point_type="bar", y1=overrides, y2=overrides)
    y1, y2 = plotter._axis_style(plotter.y1), plotter._axis_style(plotter.y2)
    for key in ("curviness", "point_type", "colors", "line_width"):
        assert getattr(y1, key) == getattr(y2, key) == overrides[key]


def test_linestyle_presets_keep_the_package_dash():
    # '--' and solid keep our own dash: scaled to the line, spaced by dash_spacing.
    plotter = ReactionProfilePlotter(line_width=2.0, dash_spacing=3.0)
    dashed = plotter._line_kwargs(plotter._axis_style({"linestyle": "--"}), "A")
    assert dashed["dashes"] == (2.0, 3.0)
    assert dashed["dash_capstyle"] == "round"


@pytest.mark.parametrize("spec", ["-.", ":", "dashdot", (0, (5, 2, 1, 2))])
def test_other_linestyles_go_straight_to_matplotlib(spec):
    plotter = ReactionProfilePlotter()
    line = plotter._line_kwargs(plotter._axis_style({"linestyle": spec}), "A")
    assert line["linestyle"] == spec
    assert "dashes" not in line  # matplotlib owns the pattern


def test_linestyle_can_be_set_per_series_on_either_axis():
    plotter = ReactionProfilePlotter(linestyle={"A": "--", "B": ":"})
    for axis in (plotter._axis_style(plotter.y1), plotter._axis_style(plotter.y2)):
        assert plotter._line_kwargs(axis, "A")["linestyle"] == "dashed"
        assert plotter._line_kwargs(axis, "B")["linestyle"] == ":"
        assert plotter._line_kwargs(axis, "C")["linestyle"] == "solid"


def test_legend_prop_overrides_the_plot_font():
    # We pass `prop` ourselves to carry the font family, so a user `prop` must merge
    # with it rather than replace it.
    plotter = ReactionProfilePlotter(font_size=12)
    font = plotter._legend_font({"prop": {"weight": "normal"}})
    assert font.get_weight() == "normal"
    assert font.get_size() == 12  # size and family still come from the plot


def test_legend_fontsize_wins_over_prop_size():
    plotter = ReactionProfilePlotter()
    font = plotter._legend_font({"prop": {"size": 20}, "fontsize": 9})
    assert font.get_size() == 9


def test_unknown_legend_prop_key_is_rejected():
    with pytest.raises(TypeError, match="Unknown font property 'wieght'"):
        ReactionProfilePlotter()._legend_font({"prop": {"wieght": "normal"}})


@pytest.mark.parametrize("axis", ["y1", "y2"])
def test_unknown_axis_key_is_rejected(axis):
    # An unknown style key must raise, not be logged and dropped.
    with pytest.raises(TypeError, match=f"Unknown {axis} key"):
        ReactionProfilePlotter(**{axis: {"colour": "viridis"}})


def test_outside_legend_with_a_right_hand_loc_warns(caplog):
    # bbox_to_anchor turns `loc` into "anchor this corner", so a right-hand loc pins the
    # legend's right edge beside the axes and the box extends back over the plot.
    ReactionProfilePlotter(labels=False, legend={"outside": True, "loc": "lower right"}).plot(ENERGIES)
    assert "overlap the plot" in caplog.text


def test_outside_legend_with_a_left_hand_loc_is_quiet(caplog):
    ReactionProfilePlotter(labels=False, legend={"outside": True, "loc": "upper left"}).plot(ENERGIES)
    assert "overlap the plot" not in caplog.text


def test_y1_label_overrides_the_units_and_energy_label():
    plotter = ReactionProfilePlotter(y1={"label": "custom"})
    assert plotter._axis_style(plotter.y1).label == "custom"


def test_axes_none_hides_the_secondary_axis():
    # twinx() creates its own spines, which `axes` must govern too.
    _, ax = plt.subplots()
    ax2, _ = ReactionProfilePlotter(axes="None", y2={"label": "r"})._draw_secondary(ax, {"bond": [1.5, 2.2, 1.6]}, [])
    assert not any(spine.get_visible() for spine in ax2.spines.values())


def test_plot_args_are_read_off_the_signature():
    # _PLOT_ARGS is read off the signature, so every plot() argument must route there.
    import inspect

    from plotprofile.plot import _PLOT_ARGS

    params = set(inspect.signature(ReactionProfilePlotter.plot).parameters) - {"self", "energy_data"}
    assert params == set(_PLOT_ARGS)


def test_plot_reaction_profile_routes_plot_args(tmp_path):
    plot_reaction_profile(
        {"a": [0.0, 5.0, 2.0]},
        x=[1.0, 2.0, 3.0],  # a plot() arg, not a style key
        curviness=0.0,  # a style key
        filename=str(tmp_path / "p"),
        dpi=72,
    )
    assert (tmp_path / "p.png").exists()


def test_plot_reaction_profile_accepts_style_kwargs(tmp_path):
    # Style keys must route to the constructor, not to plot().
    plot_reaction_profile(ENERGIES, curviness=0.0, units="kj", y2={"label": "r"}, filename=str(tmp_path / "p"), dpi=72)
    assert (tmp_path / "p.png").exists()


def test_x_places_points_at_real_coordinates(tmp_path):
    # A scan with uneven steps must not be drawn evenly spaced.
    r = [1.5, 1.8, 2.1, 2.2, 2.4, 3.5, 4.5]
    plotter = ReactionProfilePlotter(curviness=0.0, labels=False, x_indices=True, axes="both")
    plotter.plot({"scan": [0.0, 4.0, 9.0, 11.0, 12.6, 3.0, 1.0]}, x=r, filename=str(tmp_path / "p"), dpi=72)

    lo, hi = plt.gca().get_xlim()
    # the axis spans the real coordinate, not 0..n-1
    assert lo < min(r)
    assert hi > max(r)


def test_x_interpolates_repeats_and_gaps():
    # generate_coordinates puts a repeated value at a fractional index, so mapping onto
    # x has to interpolate: index 1.5 is the midpoint of x[1] and x[2].
    mapped = ReactionProfilePlotter()._x_positions([0, 1.5, 3], [10.0, 20.0, 30.0, 40.0])
    assert mapped == [10.0, 25.0, 40.0]


def test_x_without_values_is_the_index():
    assert ReactionProfilePlotter()._x_positions([0, 1.5, 3], None) == [0, 1.5, 3]


def test_x_must_cover_every_point():
    with pytest.raises(ValueError, match="longest series has 3 points"):
        ReactionProfilePlotter().plot({"a": [0.0, 1.0, 2.0]}, x=[0.0, 1.0])


def test_x_must_be_numeric():
    with pytest.raises(TypeError, match="must be a sequence of numbers"):
        ReactionProfilePlotter().plot({"a": [0.0, 1.0]}, x=["a", "b"])


def _all_text_inside(ax):
    """Every label sits within the axes, measured after drawing."""
    fig = plt.gcf()
    fig.canvas.draw()
    inverse = ax.transData.inverted()
    low, high = ax.get_ylim()
    for text in ax.texts:
        extent = (text.get_bbox_patch() or text).get_window_extent()
        y0 = inverse.transform((extent.x0, extent.y0))[1]
        y1 = inverse.transform((extent.x1, extent.y1))[1]
        if y0 < low or y1 > high:
            return False
    return True


@pytest.mark.parametrize(
    ("font_size", "figsize"),
    [(12, (5, 4.5)), (22, (3.2, 2.6)), (8, (10, 3))],
)
def test_labels_fit_the_axes_at_any_font_and_figure_size(font_size, figsize):
    # The room made for labels must follow the rendered text, not the energy range.
    ReactionProfilePlotter(font_size=font_size, figsize=figsize, axes="box", show_legend=False).plot(
        {"1": [0.0, 12.5, 2.9, 10.0]}, point_labels={"1": ["Start", "TS1", "Int", "TS2"]}
    )
    assert _all_text_inside(plt.gca())


def test_label_side_follows_its_own_curve_not_the_tallest_series():
    # A label's side follows the bend of its own curve, not whichever series is highest
    # at that x: A's -1.5 is a valley of A and goes below, its 2.0 is a peak and goes above.
    ReactionProfilePlotter().plot(
        {
            "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5, 2.0, -7.2],
            "Pathway B": [None, -2.0, 6.2, 4.3, 5.8, 2.0],
        }
    )
    sides = {t.get_text(): t.get_position()[1] for t in plt.gca().texts}
    assert sides["10.2"] > 10.2  # a peak: above
    assert sides["−1.5"] < -1.5  # a valley: below  # noqa: RUF001
    assert sides["2.0"] > 2.0  # a peak of A: above


def test_an_end_of_a_curve_takes_the_side_with_space():
    # An end has a slope but no bend, so its own shape says little: prefer open space. C is
    # the lowest curve at x=5, so nothing is under its last point, and the label reads
    # better there -- even though the curve arrives rising, which would put it above.
    #
    # An interior point keeps its own bend: B's 6.2 is a peak of B and stays above,
    # though A runs above it at that x.
    ReactionProfilePlotter().plot(
        {
            "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5, 2.0, -7.2],
            "Pathway B": [None, -2.0, 6.2, 4.3, 5.8, 2.0],
            "Pathway C": [None, -2.0, -6.8, -6.8, None, -2.0],
        }
    )
    sides = {t.get_text(): t.get_position()[1] for t in plt.gca().texts}
    assert sides["−2.0"] < -2.0  # C's last point: below, into the space  # noqa: RUF001
    assert sides["6.2"] > 6.2  # B's peak: above, bend wins


def test_point_labels_work_without_value_labels():
    # point_labels must draw with labels=False: an IRC wants the TS named, not every value.
    ReactionProfilePlotter(labels=False, show_legend=False).plot(
        {"1": [0.0, 12.5, 2.9]}, point_labels={"1": ["Start", "TS1", "Int"]}
    )
    drawn = {t.get_text() for t in plt.gca().texts}
    assert drawn == {"Start", "TS1", "Int"}


def test_multiline_annotation_fits_inside_the_axes():
    # The annotation's white background masks whatever it overhangs, so the axes must make
    # room for the label's rendered height, not a fixed fraction of the energy range.
    plotter = ReactionProfilePlotter(figsize=(4.5, 4), axes="box", show_legend=False)
    plotter.plot({"1": [-3.0, 12.5, 2.9, 0.0]}, annotations={"Step 1\nAlternate": (0, 3)})

    ax = plt.gca()
    assert _all_text_inside(ax)


def test_unparseable_energy_is_rejected():
    with pytest.raises(ValueError, match="Could not convert string to float"):
        ReactionProfilePlotter().plot({"A": [0.0, "not-a-number"]})


@pytest.mark.parametrize("data", [{}, {"A": [None]}, {"A": [None], "B": [None, None]}, []])
def test_no_plottable_energies_is_rejected(data):
    with pytest.raises(ValueError, match="No energies to plot"):
        ReactionProfilePlotter().plot(data)

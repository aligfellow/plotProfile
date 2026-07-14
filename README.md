# plotprofile 
Python code for quick plotting of professional looking reaction profiles with various customisation options available

More information can be found at [ReadTheDocs](https://plotprofile.readthedocs.io/)

[![PyPI Downloads](https://static.pepy.tech/badge/plotprofile)](https://pepy.tech/projects/plotprofile)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/aligfellow/plotprofile/ci.yml?branch=main&logo=github-actions)](https://github.com/aligfellow/plotprofile/actions)
[![License](https://img.shields.io/github/license/aligfellow/plotprofile)](https://github.com/aligfellow/plotprofile/blob/main/LICENSE)
[![Powered by: uv](https://img.shields.io/badge/-uv-purple)](https://docs.astral.sh/uv)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Typing: ty](https://img.shields.io/badge/typing-ty-EFC621.svg)](https://github.com/astral-sh/ty)

## Installation
### Google Colab
Can be used with `colab.ipynb` without a local install.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aligfellow/plotprofile/blob/main/examples/colab.ipynb)

### Pip
Simplest installation:
```bash
pip install plotprofile
```
or from the latest version:
```bash
pip install git+https://github.com/aligfellow/plotprofile.git
```
### Local installation
```bash
git clone git@github.com:aligfellow/plotprofile.git
cd plotprofile
pip install .
```

## Minimal Python Usage 
```python
from plotprofile import ReactionProfilePlotter

energy_sets = {
    "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5, 2.0, -7.2],
    "Pathway B": [None, -2.0, 6.2, 4.3, 5.8, 2.0],
}

plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename="images/profile0")
```
<img src="./examples/images/profile0.png" height="300" alt="Example 0">

## Further Python Examples
### Example 1
```python
from plotprofile import ReactionProfilePlotter

energy_sets = {
    "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5, 2.0, -7.2],
    "Pathway B": [None, -2.0, 6.2, 4.3, 5.8, 2.0],
    "Pathway C": [None, -2.0, -6.8,-6.8, None, -2.0],
    "diastereomer": [None, None, 12.2],
    "diastereomer2": [None, None, 9.8, 9.8]
}
annotations = {
    'Step 1': (0,3),
    'Step 2': (3,5),
    'Step 3': (5,6),
}

plotter = ReactionProfilePlotter(linestyle={"Pathway C": "--"})
plotter.plot(energy_sets, annotations=annotations, filename="images/profile1")
```
Passing in `annotations` for labelling of the reaction profile:
- this is done in the plotting function rather than the class
- using dictionary with keys of labels and a tuple of the start and end x-indices
- allowing for multiple plots of the same style with different annotations

<img src="./examples/images/profile1.png" height="300" alt="Example 1">

### Example 2 
A variety of other paremters can be tuned for the plotting, including:
- `axes="box|y|x|both|None"` 
- `curviness=0.42` - reduce for less curve and vice versa
- `colors=["list","of","colors"]|cmap` - specify colour list or colour map
    - if the colour list is too short then colours will be repeated. 
    - if the cmap is invalid, `viridis` will be set as a default
- `linestyle` - a matplotlib linestyle for every series, or a dict of them keyed by series label. `'--'` and solid use the package's own dash (scaled to the line, spaced by `dash_spacing`); `'-.'`, `':'` and `(offset, (on, off))` tuples go straight to matplotlib
- `show_legend=Bool`
- `legend={...}` - passed straight to matplotlib's `ax.legend()`, so `loc`, `frameon`, `fontsize`, `ncols`, `title`, `framealpha` etc. all work
- `units="kj|kcal"`
- `energy="e|electronic|g|gibbs|h|enthalpy|s|entropy|"`
- `x_label` and `y_label` can be used to set cutoms axis labels, **superceeding** `units` or `energy`

Using `style="presentation"` which sets a larger `figsize=(X,X)` with thicker lines and a larger font size:
```python
plotter = ReactionProfilePlotter(style="presentation", linestyle={"Pathway B": "--"}, point_type='dot', desaturate=False, colors='Blues_r', show_legend=False, curviness=0.5, x_label='Reaction Profile', y_label='Free Energy (kcal/mol)')
plotter.plot(energy_sets, filename="images/profile2")
```

<img src="./examples/images/profile2.png" height="300" alt="Example 2">

### Example 3 
- Straight lines set in a style, which can also be done by passing in `curviness=0`
- Labels can be placed below the annotation arrow 
- Some parameters regarding the plotting data can be tuned in `ReactionProfilePlotter.plot`:
    - `include_keys` - only some of the energy_sets keys() included in the plot
    - `exclude_from_legend` - excluded one of the energy_sets key from the legend

```python
plotter = ReactionProfilePlotter(style="straight", figsize=(6,4), linestyle={"Pathway C": "--"}, point_type='bar', annotation_color='black', axes='y', colors=['midnightblue', 'slateblue', 'darkviolet'], energy='electronic', units='kj', annotation_below_arrow=True, dash_spacing=5.0, desaturate=False)
plotter.plot(energy_sets, annotations=annotations, filename="images/profile3", exclude_from_legend=["Pathway B"], include_keys=["Pathway A", "Pathway B", "Pathway C", "diastereomer"])
```

<img src="./examples/images/profile3.png" height="300" alt="Example 3">

### Example 4 
- Point labels can be also added by passing `point_labels` to `ReactionProfilePlotter.plot`
- Annotations can accomodate newline characters `\n` and spacing will be adjusted automatically

```python
from plotprofile import ReactionProfilePlotter

energy_sets = {
    "1": [-3.0, 12.5, 2.9, 0.0, 1.8, 10.5, 2.9]
}

annotations = {
    'Step 1': (0,3),
    'Step 2\nAlternate': (3,6),
}

point_labels = {
    "1": [None, "TS1", None, "Int1", None, "TS2"]
}

plotter = ReactionProfilePlotter(figsize=(4.5,4), axes='box', show_legend=False)
plotter.plot(energy_sets, annotations=annotations, point_labels=point_labels, filename="images/profile4")
```

<img src="./examples/images/profile4.png" height="300" alt="Example 4">

### Example 5 
- Bar lengths and widths can be adjusted
- Default line/curve behaviour with bars is to connect at the edges, this can be turned off with `connect_bar_ends=False`
- Dash spacing of the line can be changed with `dash_spacing` 


```python
from plotprofile import ReactionProfilePlotter

energy_sets = {
    "1": [-3.0, 12.5, 2.9, 0.0, 1.8, 10.5, 2.9]
}

annotations = {
    'Step 1': (0,3),
    'Step 2\nAlternate': (3,6),
}

point_labels = {
    "1": [None, "TS1", None, "Int1", None, "TS2"]
}

plotter = ReactionProfilePlotter(figsize=(4.5,4), axes='box', curviness=0.5, show_legend=False, point_type='bar', bar_length=0.3, bar_width=3, connect_bar_ends=False, linestyle={"1": "--"}, dash_spacing=1.5)
plotter.plot(energy_sets, annotations=annotations, point_labels=point_labels, filename="images/profile5")
```
<img src="./examples/images/profile5.png" height="300" alt="Example 5">


### Example 6
`secondary={label: [values]}` in `plot()` adds a right-hand axis, for quantities that share the reaction coordinate but not the units. Same x-indices, same legend.

Style keys set **both** axes. `y1` and `y2` take the same keys and override one axis alone; `y2` defaults to its own palette and `linestyle='--'`.

```python
plotter = ReactionProfilePlotter(figsize=(7.6,4), curviness=0.0, labels=False, energy='E', square=True,
                                 x_label='reaction coordinate  λ',
                                 legend={'outside': True, 'anchor': 1.22},
                                 y2={'label': 'bond length (Å)', 'colors': 'plasma'})
plotter.plot({"force field": [0.0, 5.2, 12.4, 3.1, -1.2], "g-xTB": [0.0, 4.4, 10.9, 2.0, -2.5]},
             secondary={"C1-O3 (breaking)": [1.43, 1.62, 2.10, 2.85, 3.30],
                        "C1-O14 (forming)": [3.20, 2.75, 2.05, 1.55, 1.42]},
             filename="images/profile24")
```
<img src="./examples/images/profile24.png" height="300" alt="Example 6">

`y2` takes `colors`, `curviness`, `linestyle`, `line_width`, `marker_size`, `point_type`, `bar_length`, `bar_width`, `connect_bar_ends`, `desaturate`, `desaturate_factor` and `dash_spacing`:
```python
ReactionProfilePlotter(curviness=0.0, point_type='bar',                                    # both axes
                       y2={'point_type': 'dot', 'curviness': 0.42, 'linestyle': 'solid'})  # right axis only
```

### Example 7
`legend` is passed to matplotlib's `ax.legend()`, so `frameon`, `edgecolor`, `facecolor`, `framealpha`, `labelcolor`, `ncols`, `title`, `bbox_to_anchor` etc. all work. Plus two extras: `outside=True` puts the legend beside the axes (`anchor` sets how far), and `frameon` defaults to on inside, off outside.

The plot font is bold by default, and the legend inherits it. Use matplotlib's `prop` to unbold the legend alone:

```python
plotter = ReactionProfilePlotter(labels=False, legend={
    'loc': 'lower left',
    'frameon': True, 'edgecolor': 'maroon', 'facecolor': 'whitesmoke',  # border
    'labelcolor': 'darkcyan',                                           # text colour
    'prop': {'weight': 'normal'},                                       # not bold
    'fontsize': 9,
})
plotter.plot(energy_sets, filename="images/profile25")
```
<img src="./examples/images/profile25.png" height="300" alt="Example 7">

See [examples/example.ipynb](./examples/example.ipynb)

## Scans and IRCs
By default the x-axis is the point index, evenly spaced, which is what a schematic profile wants. For a scan or an IRC it is a real quantity, so pass `x` to `plot()`:

```python
r = [1.5, 1.8, 2.1, 2.2, 2.4, 3.5, 4.5]          # uneven steps, dense near the TS
E = [0.0, 4.0, 9.0, 11.0, 12.6, 3.0, 1.0]

plotter = ReactionProfilePlotter(
    curviness=0.0,        # join the computed points directly
    labels=False,
    point_type='dot',
    x_indices=True,       # show the x ticks
    axes='both',
    x_label='r(C-Cl) / Å',
    energy='E',
)
plotter.plot({"scan": E}, x=r)
```

>[!NOTE]
>- `x` must cover every index the energies use, and applies to the secondary series too.
>- Gaps (`None`) and repeated values still work: a repeat sits at the midpoint of the two `x` values it spans.
>- `annotations` are still given in **indices**, not `x` values.
>- `bar_length` is in x-axis units, so scale it to the range of `x`.

## Saving
Plots can be saved by passing `filename` to `plotter.plot()`. The output format is controlled by `file_format` and supports any standard matplotlib format (e.g. `png`, `svg`, `pdf`, `eps`).

`svg`, `pdf` and `eps` are vector: scalable, with the text left as real text, so labels stay editable in Illustrator or Inkscape.

```python
plotter.plot(energy_sets, filename="my_profile", file_format="svg")
```

`dpi` (default 600) only applies to raster formats such as `png`; it has no meaningful effect on vector output.

```python
plotter.plot(energy_sets, filename="my_profile", file_format="png", dpi=300)
```

## Further details
>[!IMPORTANT]
>- Secondary curves can begin from after the 1st point, just need to have a `None` entry in the list of energies *e.g.* `[None, 0.0, 1.0]`
>- Individual points can be placed if this is a list with only one energy value (*e.g.* uncluttered diastereomeric TS for example, see examples)
>    - labels of theses are not added to the legend
>    - these can even be placed as individual points between two indices with `[None, 5.0, 5.0]`
>- Spacing of points on the profile can be altered by:
>    - passing the same energy twice in a row, which will place the point halfway between the two x-indices, *i.e.* Pathway C point in examples, *e.g.* `[0.0, 5.0, 5.0]`
>    - with an entry like `[0.0, None, 1.0]` which will have a line connecting indexes 0 and 2 of this list with the correct x-axis alignment
>- data types can be:
>    - dict, with labels for the legend
>    - list of lists (no labelling of different profiles)
>    - single list

## CLI
Installing gives a `plotprofile` command. Data comes in as JSON files; styling lives in a `--config` JSON whose keys are exactly the `ReactionProfilePlotter` arguments. An unknown key is an error, not a warning.

```bash
plotprofile examples/input.json -o profile -f svg
plotprofile examples/input.json --config examples/config.json --annotations examples/annotations.json
plotprofile scan.json --secondary bonds.json --x coord.json --config scan.json -o irc -f svg
```

```
plotprofile INPUT [-o OUT] [-f {png,svg,pdf,eps}] [--dpi N]
                  [--config FILE] [--secondary FILE] [--x FILE]
                  [--annotations FILE] [--point-labels FILE]
```

See [examples/config.json](./examples/config.json) and the [CLI docs](https://plotprofile.readthedocs.io/en/latest/cli.html).

## Configuration options
The behavior can be customized via `styles.json` or by passing parameters to `ReactionProfilePlotter()`.

The full set of options, and the `default`, `presentation` and `straight` presets, are in [`src/plotprofile/styles.json`](./src/plotprofile/styles.json) — also rendered in the [style docs](https://plotprofile.readthedocs.io/en/latest/json_styles.html).

## Development
Requires [uv](https://docs.astral.sh/uv/) and [just](https://github.com/casey/just).

```bash
git clone https://github.com/aligfellow/plotprofile.git
cd plotprofile
just setup   # install dev dependencies and pre-commit
just check   # lint + type-check + tests
```

| Command | Description |
|---|---|
| `just check` | Run lint + type-check + tests |
| `just lint` | Format and lint with ruff |
| `just type` | Type-check with ty |
| `just test` | Run pytest with coverage |
| `just fix` | Auto-fix lint issues |
| `just build` | Build distribution |
| `just setup` | Install all dev dependencies |

GitHub Actions runs the same checks on every push to `main` and every PR.

Generated from [aligfellow/python-template](https://github.com/aligfellow/python-template); pull in later template changes with `copier update --trust`.

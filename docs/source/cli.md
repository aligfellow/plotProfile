# CLI

Installing the package gives you a `plotprofile` command. `python -m plotprofile` works too.

Data comes in as JSON files. Styling lives in a `--config` JSON file whose keys are exactly the {class}`~plotprofile.plot.ReactionProfilePlotter` keyword arguments. Anything the config cannot express, use the Python API for.

```text
plotprofile INPUT [-o OUT] [-f {png,svg,pdf,eps}] [--dpi N]
                  [--config FILE] [--secondary FILE] [--x FILE]
                  [--annotations FILE] [--point-labels FILE]
```

## Data

| Flag | Description |
|------|-------------|
| `INPUT` | JSON energies: `{"Pathway A": [0.0, 12.5, 2.9]}`, a bare list, or a list of lists. `null` leaves a gap. |
| `--secondary` | JSON series for the right-hand axis, e.g. bond lengths. See [Secondary Axis](usage/secondary-axis.md). |
| `--x` | JSON list of real x coordinates, for a scan or an IRC. See [Data Input](usage/data-input.md). |
| `--annotations` | JSON object of segment annotations, `{"Step 1": [0, 3]}`. Given in **indices**. |
| `--point-labels` | JSON object of per-point labels. |

## Styling

```bash
plotprofile examples/input.json --config examples/config.json --annotations examples/annotations.json
```

`examples/config.json`:

```json
{
  "curviness": 0.42,
  "point_type": "hollow",
  "linestyle": {"Pathway B": "--"},
  "axes": "box",
  "units": "kcal",
  "energy": "G",
  "legend": {"loc": "upper right", "prop": {"weight": "normal"}}
}
```

Nested keys work as they do in Python, so `legend`, `y1` and `y2` are objects.

```{note}
An unknown key is an error, not a warning: a typo that is merely logged gives a plot that is silently wrong.
```

## A scan

```bash
plotprofile scan.json --secondary bonds.json --x coord.json --config scan_style.json -o irc -f svg
```

`svg` (or `pdf`) is what you want for a paper figure: vector, with the text left as real text. `--dpi` applies to `png` only.

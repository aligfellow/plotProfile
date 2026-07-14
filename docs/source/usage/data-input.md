# Data Input

This outlines the data types that are required for plotting with `plotprofile`.

## Energies

The energies can be provided in the following formats:

```python
dict[str, list[float | None]]
```

A dictionary where the keys are pathway names and the values are lists of energies.

```python
list[list[float | None]]
```

A list of lists, where each inner list represents a pathway's energies. A legend will not be plotted as there are no pathway names or labels.

```python
list[float | None]
```

A single list of energies, which will be plotted as a single pathway. Again, no legend will be plotted.

## Scans and IRCs

By default the x-axis is the point index, so points are drawn evenly spaced. That is what a schematic profile wants, where the x-axis carries no quantity.

For a scan or an IRC the x-axis *is* a quantity, so pass `x` to `plot()`:

```python
r = [1.5, 1.8, 2.1, 2.2, 2.4, 3.5, 4.5]      # uneven steps, dense near the TS
E = [0.0, 4.0, 9.0, 11.0, 12.6, 3.0, 1.0]

plotter = ReactionProfilePlotter(
    curviness=0.0,        # join the computed points directly
    labels=False,
    point_type="dot",
    x_indices=True,       # show the x ticks
    axes="both",
    x_label="r(C-Cl) / Å",
    energy="E",
)
plotter.plot({"scan": E}, x=r)
```

Without `x` those seven points would be evenly spaced, so the dense sampling near the transition state would look no different from the coarse sampling at long range. `curviness=0.0` is worth setting too, so the line joins the computed points rather than interpolating between them.

Bond lengths against the same reaction coordinate go on the right-hand axis - see [Secondary Axis](secondary-axis.md).

```{note}
- `x` must cover every index the energies use, and applies to the secondary series too.
- Gaps (`None`) and repeated values still work: a repeat sits at the midpoint of the two `x` values it spans.
- `annotations` are still given in **indices**, not `x` values.
- `bar_length` is in x-axis units, so scale it to the range of `x`.
```

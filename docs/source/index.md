# plotprofile documentation

Plot publication-quality reaction profiles from computed energies: multiple pathways, isolated transition states, segment annotations, and a secondary axis for quantities that share the reaction coordinate.

```{image} https://static.pepy.tech/badge/plotprofile
:target: https://pepy.tech/projects/plotprofile
```

## Quick Example

```python
from plotprofile import ReactionProfilePlotter

energy_sets = {
    "Pathway A": [0.00, -2.0, 10.2, 1.4, -1.5, 2.0, -7.2],
    "Pathway B": [None, -2.0, 6.2, 4.3, 5.8, 2.0],
}

plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename="../images/profile0")
```

```{image} ./images/profile0.png
:height: 300
:alt: Example 0
```

```{toctree}
:maxdepth: 4
:caption: Getting Started
:hidden:

installation
quickstart
```

```{toctree}
:maxdepth: 4
:caption: User Guide
:hidden:

usage/data-input
usage/styles
usage/behaviour
usage/customisation
usage/secondary-axis
```

```{toctree}
:maxdepth: 4
:caption: Reference
:hidden:

json_styles
cli
modules
```

from pathlib import Path

import matplotlib.pyplot as plt

from plotprofile import ReactionProfilePlotter

IMAGES = Path(__file__).parent / "images"

# -------------------------------
# Behaviour Examples
# -------------------------------
# 1. Point repeated for spacing
energy_sets = {
    "Pathway A": [0.0, 5.0, 5.0, 2.0],
    "Pathway B": [0.0, 3.0, 1.0, 4.0],
}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "behaviour1")
plt.close("all")

# 2. Skipping an index
energy_sets = {
    "Pathway A": [0.0, 5.0, 2.0, 3.0],
    "Pathway B": [1.0, None, 4.0, 6.0],
}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "behaviour2")
plt.close("all")

# 3. Starting later
energy_sets = {
    "Pathway A": [0.0, -2.0, 5.0, 4.0],
    "Pathway B": [None, None, 3.0, 6.0],
}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "behaviour3")
plt.close("all")

# 4. Finishing earlier
energy_sets = {
    "Pathway A": [0.0, -2.0, 5.0, 4.0],
    "Pathway B": [0.0, 2.0, 3.0],
}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "behaviour4")
plt.close("all")

# 5. Single isolated points
energy_sets = {
    "Pathway A": [0.0, 5.0, -2.0, 4.0],
    "TS1": [None, 7.0],
}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "behaviour5")
plt.close("all")


# -------------------------------
# Plotting Examples
# -------------------------------
energy_sets = {
    "Pathway A": [0.0, -2.0, 10.0, 1.5, -1.5, 2.0, -7.0],
    "Pathway B": [None, -2.0, 6.0, 4.0, 5.0, 2.0, None],
}

plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename=IMAGES / "profile10")
plt.close("all")

# Presentation style
plotter = ReactionProfilePlotter(style="presentation")
plotter.plot(energy_sets, filename=IMAGES / "profile11")
plt.close("all")

# Straight lines style
plotter = ReactionProfilePlotter(style="straight")
plotter.plot(energy_sets, filename=IMAGES / "profile12")
plt.close("all")

# Axes display example
plotter = ReactionProfilePlotter(axes="y")
plotter.plot(energy_sets, filename=IMAGES / "profile13")
plt.close("all")

# Axis labels and units
plotter = ReactionProfilePlotter(energy="E", units="kcal", x_label="Reaction")
plotter.plot(energy_sets, filename=IMAGES / "profile14")
plt.close("all")

# Point type example
plotter = ReactionProfilePlotter(point_type="dot")
plotter.plot(energy_sets, filename=IMAGES / "profile16")
plt.close("all")

# Bar plot example
plotter = ReactionProfilePlotter(point_type="bar", bar_width=3.0, bar_length=0.3, connect_bar_ends=True)
plotter.plot(energy_sets, filename=IMAGES / "profile17")
plt.close("all")

# Dashed lines
plotter = ReactionProfilePlotter(linestyle={"Pathway A": "--"})
plotter.plot(energy_sets, filename=IMAGES / "profile18")
plt.close("all")

# Curviness
plotter = ReactionProfilePlotter(curviness=0.7)
plotter.plot(energy_sets, filename=IMAGES / "profile19")
plt.close("all")

# Colors
plotter = ReactionProfilePlotter(colors="Reds_r", desaturate=False)
plotter.plot(energy_sets, filename=IMAGES / "profile20")
plt.close("all")

# Saturation
plotter = ReactionProfilePlotter(desaturate=False)
plotter.plot(energy_sets, filename=IMAGES / "profile21")
plt.close("all")

# Annotations
annotations = {"Part 1": (0, 2), "Part 2": (2, 4), "Part\n 3": (4, 6)}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, annotations=annotations, filename=IMAGES / "profile22")
plt.close("all")

# Labels
point_labels = {"Pathway A": ["Int1", "Int2", "TS1", "Int3"], "Pathway B": [None, None, "TS2"]}
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, point_labels=point_labels, filename=IMAGES / "profile23")
plt.close("all")


# Legend example
energy_sets = {
    "Pathway A": [0.0, -2.0, 10.0, 1.5, -1.5, 2.0, -7.0],
    "Pathway B": [None, -2.0, 6.0, 4.0, 5.0, 2.0, None],
    "Pathway C": [0.0, 3.0, 5.0, 2.0, 4.0, 1.0, -3.0],
}
plotter = ReactionProfilePlotter(show_legend=True)
plotter.plot(
    energy_sets,
    exclude_from_legend=["Pathway A"],
    include_keys=["Pathway A", "Pathway C"],
    filename=IMAGES / "profile15",
)
plt.close("all")

# Secondary axis: bond lengths share the reaction coordinate with the energies,
# but not the unit, so they go on a right-hand axis.
# Style keys set both axes; `y2` overrides them for the right-hand one alone.
scan_energies = {
    "FF": [0.0, 5.2, 12.4, 3.1, -1.2],
    "SQM": [0.0, 4.4, 10.9, 2.0, -2.5],
}
bond_lengths = {
    "C1-O3 (breaking)": [1.43, 1.62, 2.10, 2.85, 3.30],
    "C1-O14 (forming)": [3.20, 2.75, 2.05, 1.55, 1.42],
}

plotter = ReactionProfilePlotter(
    figsize=(7.6, 4),
    curviness=0.4,
    labels=False,
    energy="E",
    units="kcal",
    square=True,
    x_label="reaction coordinate  λ",
    legend={"outside": True, "anchor": 1.2},
    y2={"label": "bond length (Å)", "colors": ["royalblue", "magenta"]},
)
plotter.plot(scan_energies, secondary=bond_lengths, filename=IMAGES / "profile24")

# Legend customisation
energy_sets = {
    "Pathway A": [0.0, -2.0, 10.0, 1.5, -1.5, 2.0, -7.0],
    "Pathway B": [None, -2.0, 6.0, 4.0, 5.0, 2.0, None],
    "Pathway C": [0.0, 3.0, 5.0, 2.0, 4.0, 1.0, -3.0],
}
plotter = ReactionProfilePlotter(
    labels=False,
    legend={
        "loc": "lower left",
        "frameon": True,
        "edgecolor": "maroon",
        "facecolor": "whitesmoke",
        "labelcolor": "darkcyan",
        "prop": {"weight": "normal"},
        "fontsize": 9,
    },
)
plotter.plot(energy_sets, filename=IMAGES / "profile25")
plt.close("all")

# Plotting Styles

There are some predefined styles available in the package that can be used to change the appearance of the plots. You can also create your own styles by defining a dictionary with the desired parameters.

## 1. Default Style

The default style is applied automatically when you create a `ReactionProfilePlotter` instance without specifying a style.

```python
plotter = ReactionProfilePlotter()
plotter.plot(energy_sets, filename="../images/profile10")
```

```{image} ../images/profile10.png
:height: 300px
:alt: Example 1
```

## 2. Presentation Style

This style is designed to increase the size of the plot, font size and line width, making it more suitable for presentations.

```python
plotter = ReactionProfilePlotter(style="presentation")
plotter.plot(energy_sets, filename="../images/profile11")
```

```{image} ../images/profile11.png
:height: 300px
:alt: Example 1
```

## 3. Straight Lines Style

This style inherits the default style but with straight lines instead of curved.

```python
plotter = ReactionProfilePlotter(style="straight")
plotter.plot(energy_sets, filename="../images/profile12")
```

```{image} ../images/profile12.png
:height: 300px
:alt: Example 1
```

# json styles

There are a few preset styles available for use directly, allowing for quick customisation of the plot appearance.

These are stored in a JSON file, which can be found at `src/plotprofile/styles.json`. The keys in this file are the style names, and the values are dictionaries containing the styling options.

Each of these keys can be altered when passed into the `ReactionProfilePlotter()` class, or you can create your own custom style by passing a dictionary with any changed keys.

```{literalinclude} ../../src/plotprofile/styles.json
:language: json
```

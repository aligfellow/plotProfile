"""Command line entry point: plot a reaction profile from JSON files."""

import argparse
import json
import sys
from pathlib import Path

from .plot import ReactionProfilePlotter

EPILOG = """\
Energies are {"Pathway A": [0.0, 12.5, 2.9]}, a bare list, or a list of lists;
null leaves a gap.

Styling lives in --config, a JSON object whose keys are exactly the
ReactionProfilePlotter keyword arguments:

    {"curviness": 0.0,
     "point_type": "dot",
     "labels": false,
     "legend": {"outside": true, "anchor": 1.25},
     "y2": {"label": "bond length", "colors": "plasma"}}

"""


def _load_json(path, what):
    """Read a JSON file, reporting the problem rather than a traceback."""
    try:
        with Path(path).open() as f:
            return json.load(f)
    except FileNotFoundError:
        raise SystemExit(f"plotprofile: {what} file not found: {path}") from None
    except json.JSONDecodeError as e:
        raise SystemExit(f"plotprofile: {what} file is not valid JSON: {path}\n  {e}") from None


def build_parser():
    """Build the argument parser."""
    p = argparse.ArgumentParser(
        prog="plotprofile",
        description="Plot a reaction profile, scan or IRC from JSON energies.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("input", help="JSON file of energies")
    p.add_argument("-o", "--output", default="reaction_profile", help="Output filename, without extension")
    p.add_argument("-f", "--format", default="png", choices=["png", "svg", "pdf", "eps"], help="Output format")
    p.add_argument("--dpi", type=int, default=600, help="Raster resolution; ignored for svg/pdf/eps")
    p.add_argument("--config", help="JSON file of style options (see below)")
    p.add_argument("--secondary", help="JSON file of series for the right-hand axis")
    p.add_argument("--x", help="JSON file of real x coordinates, for a scan or IRC")
    p.add_argument("--annotations", help='JSON file of segment annotations, {"Step 1": [0, 3]}')
    p.add_argument("--point-labels", help="JSON file of per-point labels")
    return p


def main(argv=None):
    """Plot a profile from JSON files. Returns a process exit code."""
    args = build_parser().parse_args(argv)

    energies = _load_json(args.input, "input")
    config = _load_json(args.config, "config") if args.config else {}
    secondary = _load_json(args.secondary, "secondary") if args.secondary else None
    point_labels = _load_json(args.point_labels, "point-labels") if args.point_labels else None
    x = _load_json(args.x, "x") if args.x else None

    if not isinstance(config, dict):
        raise SystemExit("plotprofile: config must be a JSON object of style options.")

    annotations = None
    if args.annotations:
        raw = _load_json(args.annotations, "annotations")
        if not isinstance(raw, dict):
            raise SystemExit('plotprofile: annotations must be a JSON object, e.g. {"Step 1": [0, 3]}')
        annotations = {label: tuple(span) for label, span in raw.items()}

    try:
        ReactionProfilePlotter(**config).plot(
            energies,
            secondary=secondary,
            x=x,
            annotations=annotations,
            point_labels=point_labels,
            filename=args.output,
            file_format=args.format,
            dpi=args.dpi,
        )
    except (TypeError, ValueError) as e:
        raise SystemExit(f"plotprofile: {e}") from None

    print(f"plotprofile: wrote {args.output}.{args.format}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

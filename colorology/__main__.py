"""Build the Colorology graph.

    python -m colorology build                 # writes graph/ from data/color_shades.csv
    python -m colorology build --out somewhere # choose the output folder
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from .dataset import load_palette
from .export import write_csv, write_grafana_frames, write_json
from .graph import build_graph


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="colorology")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="clean the palette and write the graph")
    build.add_argument("--input", default="data/color_shades.csv", type=Path)
    build.add_argument("--out", default="graph", type=Path)
    args = parser.parse_args(argv)

    palette = load_palette(args.input)
    graph = build_graph(palette)

    written = write_csv(graph, args.out)
    written.append(write_json(graph, args.out))
    written += write_grafana_frames(graph, args.out / "grafana")

    kinds = Counter(graph.nodes["kind"])
    relations = Counter(graph.edges["relation"])
    print(f"colors: {kinds['color']}  families: {kinds['family']}  attributes: {kinds['attribute']}")
    for note in palette.notes:
        print(f"  note: {note}")
    print("edges: " + ", ".join(f"{rel} {n}" for rel, n in sorted(relations.items())))
    for path in written:
        print(f"wrote {path}")


if __name__ == "__main__":
    main()

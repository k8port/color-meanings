"""Write the graph out in formats other tools can read."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .graph import ColorGraph

# Relations that connect two colors, which is what a node graph panel shows.
COLOR_RELATIONS = ["SIMILAR_TO", "COMPLEMENTS", "TRIADIC_WITH", "ANALOGOUS_TO"]


def write_csv(graph: ColorGraph, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    nodes_path, edges_path = out_dir / "nodes.csv", out_dir / "edges.csv"
    graph.nodes.to_csv(nodes_path, index=False)
    graph.edges.to_csv(edges_path, index=False)
    return [nodes_path, edges_path]


def write_json(graph: ColorGraph, out_dir: Path) -> Path:
    """Node-link JSON, the shape D3 and networkx both read."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "graph.json"
    payload = {
        "nodes": _records(graph.nodes),
        "links": _records(graph.edges),
    }
    path.write_text(json.dumps(payload, indent=1))
    return path


def write_grafana_frames(graph: ColorGraph, out_dir: Path) -> list[Path]:
    """Color-to-color graph using Grafana's node graph field names.

    The nodes frame uses id/title/subtitle/mainstat/secondarystat/color and
    detail__* fields; the edges frame uses id/source/target/mainstat. Name the
    frames "nodes" and "edges" (or set preferredVisualisationType to
    "nodeGraph") and the built-in Node Graph panel renders them directly.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    colors = graph.nodes[graph.nodes["kind"] == "color"]
    nodes = pd.DataFrame(
        {
            "id": colors["id"],
            "title": colors["label"],
            "subtitle": colors["hex"],
            "mainstat": colors["family"],
            "secondarystat": colors["temperature"],
            "color": colors["hex"],
            "detail__lightness": colors["lightness"],
            "detail__chroma": colors["chroma"],
            "detail__hue": colors["hue"],
        }
    )
    links = graph.edges[graph.edges["relation"].isin(COLOR_RELATIONS)]
    edges = pd.DataFrame(
        {
            "id": links["id"],
            "source": links["source"],
            "target": links["target"],
            "mainstat": links["relation"],
            "secondarystat": links["weight"],
            "detail__delta_e": links["weight"],
        }
    )
    paths = [out_dir / "nodes.json", out_dir / "edges.json"]
    paths[0].write_text(json.dumps(_frame("nodes", nodes), indent=1))
    paths[1].write_text(json.dumps(_frame("edges", edges), indent=1))
    return paths


def _frame(name: str, df: pd.DataFrame) -> dict:
    """A data frame in Grafana's JSON shape: named fields with value arrays."""
    return {
        "name": name,
        "meta": {"preferredVisualisationType": "nodeGraph"},
        "fields": [{"name": col, "values": _values(df[col])} for col in df.columns],
    }


def _values(series: pd.Series) -> list:
    return [None if pd.isna(v) else v for v in series.tolist()]


def _records(df: pd.DataFrame) -> list[dict]:
    return [
        {k: (None if pd.isna(v) else v) for k, v in row.items() if not (isinstance(v, str) and v == "")}
        for row in df.to_dict(orient="records")
    ]

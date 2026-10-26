"""Turn the palette into a graph of colors, families, and described attributes.

Relationships
-------------
SIMILAR_TO     two colors a person would see as close (CIEDE2000 difference)
COMPLEMENTS    the named color nearest the true complement (hue rotated 180 deg)
TRIADIC_WITH   the named color nearest a triad partner (hue rotated 120 deg)
ANALOGOUS_TO   the named color nearest a hue neighbor (hue rotated 30 deg)
IN_FAMILY      color -> its hue family (red, blue, brown, gray, ...)
DESCRIBED_AS   color -> a term its description uses (retro, calming, silk, ...)

Harmony partners are found the way a designer would: rotate the color's hue on
the HSL wheel (the one CSS and most color pickers use) while keeping its
saturation and lightness, then pick the named color that looks closest to that
ideal point, judged by perceptual (CIEDE2000) difference.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .color_math import ciede2000, hsl_to_rgb, hue_distance, rgb_to_lab
from .dataset import Palette

# Tuning knobs, kept together so the choices are easy to see and change.
SIMILAR_NEIGHBORS = 3        # nearest neighbors to link per color
SIMILAR_MAX_DELTA_E = 8.0    # beyond this two colors are no longer "similar"
HARMONY_MIN_CHROMA = 12.0    # grays have no meaningful hue to rotate
HARMONY_HUE_TOLERANCE = 15.0 # degrees a partner may sit from the ideal hue
HARMONY_MAX_DELTA_E = 15.0   # how far a partner may sit from the ideal color

HARMONIES = {
    "COMPLEMENTS": (180.0,),
    "TRIADIC_WITH": (120.0, 240.0),
    "ANALOGOUS_TO": (30.0, -30.0),
}


@dataclass
class ColorGraph:
    nodes: pd.DataFrame
    edges: pd.DataFrame


def _undirected(df: pd.DataFrame) -> pd.DataFrame:
    """Collapse A->B and B->A of the same relation into one edge."""
    a = df[["source", "target"]].min(axis=1)
    b = df[["source", "target"]].max(axis=1)
    out = df.assign(source=a, target=b)
    return out.sort_values("weight").drop_duplicates(["source", "target", "relation"])


def similar_edges(palette: Palette, delta_e: np.ndarray) -> pd.DataFrame:
    ids = palette.colors["id"].to_numpy()
    d = delta_e.copy()
    np.fill_diagonal(d, np.inf)
    nearest = np.argsort(d, axis=1)[:, :SIMILAR_NEIGHBORS]
    rows = [
        (ids[i], ids[j], float(d[i, j]))
        for i in range(len(ids))
        for j in nearest[i]
        if d[i, j] <= SIMILAR_MAX_DELTA_E
    ]
    edges = pd.DataFrame(rows, columns=["source", "target", "weight"]).assign(relation="SIMILAR_TO")
    return _undirected(edges)


def harmony_edges(palette: Palette) -> pd.DataFrame:
    colors = palette.colors
    ids = colors["id"].to_numpy()
    lab = palette.lab
    hsl = colors[["hue", "saturation", "lightness"]].to_numpy()
    hue = hsl[:, 0]
    chromatic = palette.lch[:, 1] >= HARMONY_MIN_CHROMA

    frames = []
    for relation, angles in HARMONIES.items():
        for angle in angles:
            ideal = hsl.copy()
            ideal[:, 0] = (ideal[:, 0] + angle) % 360
            ideal_lab = rgb_to_lab(hsl_to_rgb(ideal))

            # Distance from every ideal partner (rows) to every real color (cols).
            d = ciede2000(ideal_lab[:, None, :], lab[None, :, :])
            hue_off = hue_distance(ideal[:, 0][:, None], hue[None, :])
            allowed = chromatic[None, :] & (hue_off <= HARMONY_HUE_TOLERANCE)
            np.fill_diagonal(allowed, False)
            d = np.where(allowed, d, np.inf)

            best = np.argmin(d, axis=1)
            best_d = d[np.arange(len(ids)), best]
            keep = chromatic & (best_d <= HARMONY_MAX_DELTA_E)
            frames.append(
                pd.DataFrame(
                    {
                        "source": ids[keep],
                        "target": ids[best[keep]],
                        "weight": best_d[keep],
                        "relation": relation,
                    }
                )
            )
    return _undirected(pd.concat(frames, ignore_index=True))


def build_graph(palette: Palette) -> ColorGraph:
    colors = palette.colors
    delta_e = ciede2000(palette.lab[:, None, :], palette.lab[None, :, :])

    color_nodes = pd.DataFrame(
        {
            "id": colors["id"],
            "kind": "color",
            "label": colors["name"],
            "hex": colors["hex"],
            "family": colors["family"],
            "temperature": colors["temperature"],
            "lightness": colors["lab_l"].round(2),
            "chroma": colors["chroma"].round(2),
            "hue": colors["lab_hue"].round(1),
            "group": "",
        }
    )

    families = sorted(colors["family"].unique())
    family_nodes = pd.DataFrame(
        {"id": [f"family:{f}" for f in families], "kind": "family", "label": families, "group": "family"}
    )

    attr_pairs = [
        (cid, group, term)
        for cid, attrs in zip(colors["id"], colors["attributes"])
        for group, term in attrs
    ]
    attr_df = pd.DataFrame(attr_pairs, columns=["color", "group", "term"])
    attr_keys = attr_df[["group", "term"]].drop_duplicates().sort_values(["group", "term"])
    attr_nodes = pd.DataFrame(
        {
            "id": "attr:" + attr_keys["group"] + ":" + attr_keys["term"].str.replace(" ", "-"),
            "kind": "attribute",
            "label": attr_keys["term"],
            "group": attr_keys["group"],
        }
    )

    family_edges = pd.DataFrame(
        {"source": colors["id"], "target": "family:" + colors["family"], "relation": "IN_FAMILY", "weight": np.nan}
    )
    attr_edges = pd.DataFrame(
        {
            "source": attr_df["color"],
            "target": "attr:" + attr_df["group"] + ":" + attr_df["term"].str.replace(" ", "-"),
            "relation": "DESCRIBED_AS",
            "weight": np.nan,
        }
    )

    nodes = pd.concat([color_nodes, family_nodes, attr_nodes], ignore_index=True)
    edges = pd.concat(
        [similar_edges(palette, delta_e), harmony_edges(palette), family_edges, attr_edges],
        ignore_index=True,
    )
    edges["weight"] = edges["weight"].round(3)
    edges.insert(0, "id", [f"e{i}" for i in range(len(edges))])
    return ColorGraph(nodes=nodes, edges=edges)

"""Draw every color in the dataset on a hue wheel, plus one color's harmony links.

    python scripts/draw_wheel.py            # writes docs/color-wheel.png

Angle is HSL hue, distance from the center is CIELAB chroma (how colorful it
is), so grays sit in the middle and vivid colors at the rim. Each dot is drawn
in its own color.
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from colorology import build_graph, load_palette  # noqa: E402

FOCUS = "international-klein-blue"
SURFACE, INK, MUTED = "#FAFAF7", "#1F1F1F", "#6B6B6B"
HALO = [pe.withStroke(linewidth=3, foreground=SURFACE)]
LINK_STYLE = {
    "COMPLEMENTS": ("-", 2.0),
    "TRIADIC_WITH": ("--", 1.5),
    "ANALOGOUS_TO": (":", 2.0),
}


def main(out: Path = Path("docs/color-wheel.png")) -> None:
    palette = load_palette("data/color_shades.csv")
    graph = build_graph(palette)
    c = palette.colors.set_index("id")

    theta = np.radians(c["hue"].to_numpy())
    radius = c["chroma"].to_numpy()

    fig = plt.figure(figsize=(8, 8.6), facecolor=SURFACE)
    ax = fig.add_subplot(projection="polar", facecolor=SURFACE)
    ax.scatter(theta, radius, s=34, c=c["hex"].tolist(), edgecolors=SURFACE, linewidths=1.0, zorder=2)

    # One color's harmony partners, to show what the edges mean.
    edges = graph.edges
    links = edges[((edges["source"] == FOCUS) | (edges["target"] == FOCUS)) & edges["relation"].isin(LINK_STYLE)]
    links = links.assign(other=np.where(links["source"] == FOCUS, links["target"], links["source"]))
    # Keep the closest partner on each side of the wheel, so labels don't pile up.
    side = ((c.loc[links["other"], "hue"].to_numpy() - c.loc[FOCUS, "hue"]) % 360) < 180
    links = links.assign(side=side).sort_values("weight").drop_duplicates(["relation", "side"])
    f_t, f_r = np.radians(c.loc[FOCUS, "hue"]), c.loc[FOCUS, "chroma"]
    for _, e in links.iterrows():
        other = e["other"]
        style, width = LINK_STYLE[e["relation"]]
        o_t, o_r = np.radians(c.loc[other, "hue"]), c.loc[other, "chroma"]
        ax.plot([f_t, o_t], [f_r, o_r], linestyle=style, color=INK, linewidth=width, zorder=3)
        ax.scatter([o_t], [o_r], s=150, c=[c.loc[other, "hex"]], edgecolors=INK, linewidths=1.5, zorder=4)
        ax.annotate(
            c.loc[other, "name"], (o_t, o_r), xytext=(8, 6), textcoords="offset points",
            fontsize=9, color=INK, zorder=5, path_effects=HALO,
        )
    ax.scatter([f_t], [f_r], s=220, c=[c.loc[FOCUS, "hex"]], edgecolors=INK, linewidths=2, zorder=4)
    ax.annotate(
        c.loc[FOCUS, "name"], (f_t, f_r), xytext=(10, -14), textcoords="offset points",
        fontsize=10, fontweight="bold", color=INK, zorder=5, path_effects=HALO,
    )

    ax.set_theta_zero_location("E")
    ax.set_rlabel_position(150)
    ax.set_yticks([30, 60, 90, 120])
    ax.set_yticklabels(["30", "60", "90", "120"], color=MUTED, fontsize=8)
    ax.set_xticks(np.radians([0, 60, 120, 180, 240, 300]))
    ax.set_xticklabels(["0° red", "60° yellow", "120° green", "180° cyan", "240° blue", "300° magenta"],
                       color=MUTED, fontsize=9)
    ax.grid(color="#E4E4DF", linewidth=0.8)
    ax.spines["polar"].set_color("#E4E4DF")

    fig.suptitle(f"{len(c):,} named colors by hue and chroma", x=0.06, ha="left", y=0.975,
                 fontsize=15, fontweight="bold", color=INK)
    fig.text(0.06, 0.928,
             "Angle is hue; distance from the center is how colorful a color is (CIELAB chroma).\n"
             f"Lines show {c.loc[FOCUS, 'name']}'s partners: solid = complement, "
             "dashed = triadic, dotted = analogous.",
             fontsize=9.5, color=MUTED, ha="left", va="top")
    fig.subplots_adjust(top=0.84, bottom=0.04)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, facecolor=SURFACE)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

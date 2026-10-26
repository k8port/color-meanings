"""Load the scraped shades, clean them, and derive per-color properties."""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

from modules.nlp import category_mappings as cm

from .color_math import classify_family, hex_to_rgb, lab_to_lch, rgb_to_hsl, rgb_to_lab

# Words in the seasonal lists that are too generic to signal a season on their
# own ("a fresh green", "a warm orange"), so they are skipped when tagging.
_AMBIGUOUS_SEASON_WORDS = {
    "green", "orange", "new", "young", "fresh", "warm", "cool", "cold", "hot",
    "full", "mature", "ripe", "ice",
}

# Keyword groups used to tag what a description talks about.
ATTRIBUTE_GROUPS: dict[str, list[str]] = {
    "aesthetic": cm.aesthetic_keywords,
    "era": cm.historical_era_keywords,
    "material": cm.material_keywords,
    "mood": cm.emotional_keywords,
    "finish": cm.finish_keywords,
    "intensity": cm.saturation_keywords,
}


@dataclass
class Palette:
    """The cleaned color table plus its Lab/LCh arrays, aligned by row."""

    colors: pd.DataFrame
    lab: np.ndarray
    lch: np.ndarray
    dropped_duplicates: int = 0
    notes: list[str] = field(default_factory=list)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _parse_description(raw: object) -> str:
    """The scraper stored descriptions as the repr of a list of lines."""
    if not isinstance(raw, str) or not raw.strip():
        return ""
    text = raw
    try:
        parsed = ast.literal_eval(raw)
        if isinstance(parsed, (list, tuple)):
            text = " ".join(str(part) for part in parsed)
    except (ValueError, SyntaxError):
        pass
    return re.sub(r"\s+", " ", text).strip()


def _keyword_pattern(words: list[str]) -> re.Pattern[str]:
    unique = sorted({w.lower().strip() for w in words if w.strip()}, key=len, reverse=True)
    return re.compile(r"\b(" + "|".join(re.escape(w) for w in unique) + r")\b", re.IGNORECASE)


_SEASON_PATTERNS = {
    season: _keyword_pattern([w for w in words if w not in _AMBIGUOUS_SEASON_WORDS])
    for season, words in cm.seasonal_keywords.items()
}
_GROUP_PATTERNS = {group: _keyword_pattern(words) for group, words in ATTRIBUTE_GROUPS.items()}


def extract_attributes(description: str) -> list[tuple[str, str]]:
    """Return (group, term) pairs a description mentions, e.g. ("aesthetic", "retro")."""
    found: set[tuple[str, str]] = set()
    if not description:
        return []
    for season, pattern in _SEASON_PATTERNS.items():
        if pattern.search(description):
            found.add(("season", season))
    claimed: set[str] = set()  # a term listed in two groups counts once, in the first
    for group, pattern in _GROUP_PATTERNS.items():
        for match in pattern.finditer(description):
            term = match.group(1).lower()
            if term not in claimed:
                claimed.add(term)
                found.add((group, term))
    return sorted(found)


def temperature_of(lab_hue: float, chroma: float) -> str:
    """Warm (reds through yellows), cool (greens through blues), or neutral.

    Uses the perceptual LCh hue angle. Grays, and hues on the borders between
    warm and cool (yellow-greens, violets), are neutral.
    """
    if chroma < 10:
        return "neutral"
    if lab_hue < 100 or lab_hue >= 345:
        return "warm"
    if 130 <= lab_hue < 300:
        return "cool"
    return "neutral"


def load_palette(csv_path: str | Path) -> Palette:
    raw = pd.read_csv(csv_path)
    raw["name"] = raw["name"].astype(str).str.strip()
    raw["hex"] = raw["hex"].astype(str).str.strip().str.upper()

    # Same color listed twice (often on two family pages) - keep the first.
    key = raw["name"].str.lower() + "|" + raw["hex"]
    dupes = int(key.duplicated().sum())
    df = raw.loc[~key.duplicated()].reset_index(drop=True)

    rgb = np.array([hex_to_rgb(h) for h in df["hex"]])
    lab = rgb_to_lab(rgb)
    lch = lab_to_lch(lab)
    hsl = np.array([rgb_to_hsl(tuple(c)) for c in rgb])

    df["r"], df["g"], df["b"] = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    df["hue"], df["saturation"], df["lightness"] = hsl[:, 0], hsl[:, 1], hsl[:, 2]
    df["lab_l"], df["lab_a"], df["lab_b"] = lab[:, 0], lab[:, 1], lab[:, 2]
    df["chroma"], df["lab_hue"] = lch[:, 1], lch[:, 2]
    df["family"] = [
        classify_family(h, l, L, C) for (h, _, l), L, C in zip(hsl, lab[:, 0], lch[:, 1])
    ]
    df["temperature"] = [temperature_of(h, c) for c, h in zip(lch[:, 1], lch[:, 2])]
    df["description"] = df["description"].map(_parse_description)
    df["attributes"] = df["description"].map(extract_attributes)

    # Stable, readable ids. Different colors that share a name get the hex appended.
    base = df["name"].map(slugify)
    clash = base.duplicated(keep=False)
    ids = pd.Series(np.where(clash, base + "-" + df["hex"].str.lstrip("#").str.lower(), base))
    # Names that only differ in punctuation can still collide; number the repeats.
    repeat = ids.groupby(ids).cumcount()
    df["id"] = np.where(repeat > 0, ids + "-" + (repeat + 1).astype(str), ids)

    notes = [f"dropped {dupes} rows that repeated the same name and hex"]
    shared_hex = int(df["hex"].duplicated(keep=False).sum())
    if shared_hex:
        notes.append(f"{shared_hex} colors share a hex value with a differently named color")
    return Palette(colors=df, lab=lab, lch=lch, dropped_duplicates=dupes, notes=notes)

"""Color-space conversions and perceptual color difference.

Everything here is vectorized with NumPy so the whole palette (~1,400 colors)
can be compared pairwise in one pass.

Conventions
-----------
* sRGB channels are 0-255 integers on input.
* CIELAB uses the D65 white point (the sRGB reference white).
* Hue angles are degrees in [0, 360).
"""

from __future__ import annotations

import colorsys

import numpy as np

# D65 reference white, 2-degree observer, scaled so Y = 1.0
_D65 = np.array([0.95047, 1.00000, 1.08883])

# Linear sRGB -> CIE XYZ (IEC 61966-2-1)
_SRGB_TO_XYZ = np.array(
    [
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ]
)


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """'#ED2939' -> (237, 41, 57). Accepts 3- or 6-digit codes, with or without '#'."""
    h = hex_code.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    if len(h) != 6:
        raise ValueError(f"not a hex color: {hex_code!r}")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def rgb_to_hsl(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    """(r, g, b) 0-255 -> (hue degrees, saturation 0-1, lightness 0-1)."""
    r, g, b = (c / 255.0 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return (h * 360.0) % 360.0, s, l


def hsl_to_rgb(hsl: np.ndarray) -> np.ndarray:
    """(N, 3) HSL (hue degrees, sat 0-1, light 0-1) -> (N, 3) sRGB 0-255 floats."""
    return np.array(
        [colorsys.hls_to_rgb((h % 360) / 360.0, l, s) for h, s, l in np.asarray(hsl, dtype=float)]
    ) * 255.0


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """Convert an (N, 3) array of 0-255 sRGB values to (N, 3) CIELAB (D65)."""
    c = np.asarray(rgb, dtype=float) / 255.0
    # undo the sRGB transfer curve
    linear = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = linear @ _SRGB_TO_XYZ.T / _D65

    eps, kappa = 216 / 24389, 24389 / 27
    f = np.where(xyz > eps, np.cbrt(xyz), (kappa * xyz + 16) / 116)
    L = 116 * f[:, 1] - 16
    a = 500 * (f[:, 0] - f[:, 1])
    b = 200 * (f[:, 1] - f[:, 2])
    return np.stack([L, a, b], axis=1)


def lab_to_lch(lab: np.ndarray) -> np.ndarray:
    """(N, 3) Lab -> (N, 3) LCh with hue in degrees."""
    lab = np.asarray(lab, dtype=float)
    C = np.hypot(lab[:, 1], lab[:, 2])
    h = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    return np.stack([lab[:, 0], C, h], axis=1)


def lch_to_lab(lch: np.ndarray) -> np.ndarray:
    """(N, 3) LCh (hue in degrees) -> (N, 3) Lab."""
    lch = np.asarray(lch, dtype=float)
    rad = np.radians(lch[:, 2])
    return np.stack([lch[:, 0], lch[:, 1] * np.cos(rad), lch[:, 1] * np.sin(rad)], axis=1)


def hue_distance(h1: np.ndarray, h2: np.ndarray) -> np.ndarray:
    """Shortest angular distance between hue angles, in degrees (0-180)."""
    d = np.abs(np.asarray(h1, dtype=float) - np.asarray(h2, dtype=float)) % 360
    return np.minimum(d, 360 - d)


def ciede2000(lab1: np.ndarray, lab2: np.ndarray) -> np.ndarray:
    """CIEDE2000 color difference (Sharma, Wu & Dalal 2005).

    ``lab1`` and ``lab2`` broadcast against each other, so passing
    ``lab[:, None, :]`` and ``lab[None, :, :]`` yields the full N x N matrix.
    A difference under ~2.3 is roughly the smallest a person can notice.
    """
    lab1 = np.asarray(lab1, dtype=float)
    lab2 = np.asarray(lab2, dtype=float)
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]

    C1 = np.hypot(a1, b1)
    C2 = np.hypot(a2, b2)
    C_bar = (C1 + C2) / 2
    G = 0.5 * (1 - np.sqrt(C_bar**7 / (C_bar**7 + 25.0**7)))
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360

    dLp = L2 - L1
    dCp = C2p - C1p

    zero_chroma = (C1p * C2p) == 0
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, dh)
    dh = np.where(dh < -180, dh + 360, dh)
    dh = np.where(zero_chroma, 0.0, dh)
    dHp = 2 * np.sqrt(C1p * C2p) * np.sin(np.radians(dh) / 2)

    Lp_bar = (L1 + L2) / 2
    Cp_bar = (C1p + C2p) / 2
    h_sum = h1p + h2p
    h_bar = np.where(
        np.abs(h1p - h2p) <= 180,
        h_sum / 2,
        np.where(h_sum < 360, (h_sum + 360) / 2, (h_sum - 360) / 2),
    )
    h_bar = np.where(zero_chroma, h_sum, h_bar)

    T = (
        1
        - 0.17 * np.cos(np.radians(h_bar - 30))
        + 0.24 * np.cos(np.radians(2 * h_bar))
        + 0.32 * np.cos(np.radians(3 * h_bar + 6))
        - 0.20 * np.cos(np.radians(4 * h_bar - 63))
    )
    d_theta = 30 * np.exp(-(((h_bar - 275) / 25) ** 2))
    R_C = 2 * np.sqrt(Cp_bar**7 / (Cp_bar**7 + 25.0**7))
    S_L = 1 + (0.015 * (Lp_bar - 50) ** 2) / np.sqrt(20 + (Lp_bar - 50) ** 2)
    S_C = 1 + 0.045 * Cp_bar
    S_H = 1 + 0.015 * Cp_bar * T
    R_T = -np.sin(np.radians(2 * d_theta)) * R_C

    return np.sqrt(
        (dLp / S_L) ** 2
        + (dCp / S_C) ** 2
        + (dHp / S_H) ** 2
        + R_T * (dCp / S_C) * (dHp / S_H)
    )


# Hue bands (HSL degrees) for naming a color's family. These are a reproducible
# heuristic, not the source site's editorial grouping. The thresholds were
# checked against the 855 colors whose own names contain a single family word
# ("Steel Blue", "Rust Brown"); the rules agree with those names about 80% of
# the time, and most misses are genuinely ambiguous (tans, off-whites, plums).
_HUE_BANDS = [
    (15, "red"),
    (40, "orange"),
    (70, "yellow"),
    (170, "green"),
    (255, "blue"),
    (320, "purple"),
    (345, "pink"),
    (360, "red"),
]


def classify_family(hue: float, hsl_light: float, lab_l: float, chroma: float) -> str:
    """Assign a family from HSL hue/lightness plus CIELAB lightness and chroma."""
    if chroma < 10:  # too little color to have a hue
        if lab_l < 20:
            return "black"
        return "white" if lab_l > 90 else "gray"
    if lab_l < 12:
        return "black"
    # Dark oranges and golds read as brown.
    if 15 <= hue < 45 and lab_l < 55:
        return "brown"
    # Light reds read as pink.
    if (hue < 15 or hue >= 345) and hsl_light >= 0.65:
        return "pink"
    for upper, name in _HUE_BANDS:
        if hue < upper:
            return name
    return "red"

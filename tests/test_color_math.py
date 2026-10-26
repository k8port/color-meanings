import numpy as np
import pytest

from colorology.color_math import (
    ciede2000,
    classify_family,
    hex_to_rgb,
    hsl_to_rgb,
    hue_distance,
    lab_to_lch,
    lch_to_lab,
    rgb_to_hsl,
    rgb_to_lab,
)


def test_hex_to_rgb():
    assert hex_to_rgb("#ED2939") == (237, 41, 57)
    assert hex_to_rgb("fff") == (255, 255, 255)
    with pytest.raises(ValueError):
        hex_to_rgb("#12345")


def test_rgb_to_lab_reference_colors():
    lab = rgb_to_lab(np.array([[255, 255, 255], [0, 0, 0], [255, 0, 0]]))
    np.testing.assert_allclose(lab[0], [100, 0, 0], atol=0.01)
    np.testing.assert_allclose(lab[1], [0, 0, 0], atol=0.01)
    np.testing.assert_allclose(lab[2], [53.24, 80.09, 67.20], atol=0.02)


def test_lch_round_trip():
    lab = np.array([[50.0, 20.0, -30.0], [70.0, -10.0, 5.0]])
    np.testing.assert_allclose(lch_to_lab(lab_to_lch(lab)), lab, atol=1e-9)


def test_hsl_round_trip():
    rgb = np.array([[237, 41, 57], [0, 47, 167], [255, 255, 204]])
    hsl = np.array([rgb_to_hsl(tuple(c)) for c in rgb])
    np.testing.assert_allclose(hsl_to_rgb(hsl), rgb, atol=1e-6)


# Published test pairs from Sharma, Wu & Dalal (2005), "The CIEDE2000
# Color-Difference Formula: Implementation Notes, Supplementary Test Data".
SHARMA_PAIRS = [
    ((50.0000, 2.6772, -79.7751), (50.0000, 0.0000, -82.7485), 2.0425),
    ((50.0000, 3.1571, -77.2803), (50.0000, 0.0000, -82.7485), 2.8615),
    ((50.0000, 2.8361, -74.0200), (50.0000, 0.0000, -82.7485), 3.4412),
    ((50.0000, 0.0000, 0.0000), (50.0000, -1.0000, 2.0000), 2.3669),
    ((60.2574, -34.0099, 36.2677), (60.4626, -34.1751, 39.4387), 1.2644),
]


@pytest.mark.parametrize("lab1, lab2, expected", SHARMA_PAIRS)
def test_ciede2000_matches_published_values(lab1, lab2, expected):
    assert ciede2000(np.array(lab1), np.array(lab2)) == pytest.approx(expected, abs=1e-4)


def test_ciede2000_is_symmetric_and_zero_on_identity():
    lab = rgb_to_lab(np.array([[237, 41, 57], [0, 47, 167], [128, 128, 128]]))
    d = ciede2000(lab[:, None, :], lab[None, :, :])
    np.testing.assert_allclose(d, d.T, atol=1e-9)
    np.testing.assert_allclose(np.diag(d), 0, atol=1e-9)


def test_hue_distance_wraps_around():
    assert hue_distance(350, 10) == 20
    assert hue_distance(0, 180) == 180


@pytest.mark.parametrize(
    "hex_code, family",
    [
        ("#ED2939", "red"),     # Imperial Red
        ("#002FA7", "blue"),    # International Klein Blue
        ("#FFF000", "yellow"),  # Yellow Rose
        ("#100E09", "black"),   # Premium Black
        ("#FFF8E7", "white"),   # Cosmic Latte
        ("#808080", "gray"),
        ("#7B3F00", "brown"),   # Chocolate
        ("#FFC0CB", "pink"),
        ("#9A4EAE", "purple"),  # Purpureus
    ],
)
def test_classify_family(hex_code, family):
    rgb = hex_to_rgb(hex_code)
    h, _, l = rgb_to_hsl(rgb)
    L, C, _ = lab_to_lch(rgb_to_lab(np.array([rgb])))[0]
    assert classify_family(h, l, L, C) == family

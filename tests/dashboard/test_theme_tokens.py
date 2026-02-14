from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.dashboard.theme import get_component_colors, get_theme_tokens


def _hex_to_rgb(color: str) -> Tuple[float, float, float]:
    clean = color.strip().lstrip("#")
    if len(clean) != 6:
        raise ValueError(f"Unsupported color format: {color}")
    r = int(clean[0:2], 16) / 255.0
    g = int(clean[2:4], 16) / 255.0
    b = int(clean[4:6], 16) / 255.0
    return r, g, b


def _luminance(color: str) -> float:
    def channel(v: float) -> float:
        if v <= 0.03928:
            return v / 12.92
        return ((v + 0.055) / 1.055) ** 2.4

    r, g, b = _hex_to_rgb(color)
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def _contrast_ratio(foreground: str, background: str) -> float:
    l1 = _luminance(foreground)
    l2 = _luminance(background)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_theme_tokens_required_keys(mode: str):
    tokens = get_theme_tokens(mode)
    required_keys = {
        "bg_primary",
        "bg_card",
        "text_primary",
        "text_secondary",
        "border_light",
        "plot_bgcolor",
        "paper_bgcolor",
        "chart_grid",
        "chart_text",
        "chart_title",
        "font_family",
        "mode",
    }
    assert required_keys.issubset(tokens.keys())
    assert tokens["mode"] == mode


def test_component_colors_contract_keys():
    colors = get_component_colors("light")
    expected = {
        "walmart_blue",
        "walmart_blue_dark",
        "walmart_blue_light",
        "walmart_yellow",
        "background",
        "critical",
        "warning",
        "success",
        "text_dark",
        "text_light",
        "plot_bg",
        "paper_bg",
        "font_family",
    }
    assert expected.issubset(colors.keys())


@pytest.mark.parametrize(
    "mode,text_key,bg_key,min_ratio",
    [
        ("light", "text_primary", "bg_primary", 4.5),
        ("light", "text_secondary", "bg_card", 4.5),
        ("dark", "text_primary", "bg_primary", 4.5),
        ("dark", "text_secondary", "bg_card", 4.5),
    ],
)
def test_wcag_aa_contrast_for_core_text_pairs(mode: str, text_key: str, bg_key: str, min_ratio: float):
    tokens = get_theme_tokens(mode)
    ratio = _contrast_ratio(tokens[text_key], tokens[bg_key])
    assert ratio >= min_ratio

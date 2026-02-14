"""Theme helpers aligned with Streamlit native light/dark settings."""

from __future__ import annotations

from typing import Dict, Literal

import plotly.graph_objects as go

ThemeMode = Literal["light", "dark"]

COMMON_TOKENS: Dict[str, str] = {
    "walmart_blue": "#004C91",
    "walmart_blue_dark": "#003695",
    "walmart_blue_light": "#0071CE",
    "walmart_yellow": "#FFC220",
    "color_critical": "#EF4444",
    "color_warning": "#F59E0B",
    "color_success": "#10B981",
    "color_info": "#3B82F6",
    "font_family": "Inter, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
}

THEME_TOKENS: Dict[ThemeMode, Dict[str, str]] = {
    "light": {
        "bg_primary": "#F8FAFC",
        "bg_card": "#FFFFFF",
        "bg_sidebar": "#FFFFFF",
        "text_primary": "#111827",
        "text_secondary": "#4B5563",
        "text_muted": "#6B7280",
        "border_light": "#D1D5DB",
        "border_subtle": "#E5E7EB",
        "surface_subtle": "#FAFBFC",
        "surface_muted": "#F3F4F6",
        "surface_elevated": "#FCFCFD",
        "surface_info_soft": "#EFF6FF",
        "surface_success_soft": "#DCFCE7",
        "surface_warning_soft": "#FEF3C7",
        "surface_danger_soft": "#FEE2E2",
        "surface_danger_subtle": "#FEF2F2",
        "text_success": "#166534",
        "text_warning": "#92400E",
        "text_danger": "#991B1B",
        "border_success": "#86EFAC",
        "border_warning": "#FCD34D",
        "border_danger": "#FCA5A5",
        "plot_bgcolor": "#FFFFFF",
        "paper_bgcolor": "#FFFFFF",
        "chart_grid": "rgba(148, 163, 184, 0.25)",
        "chart_axis": "#94A3B8",
        "chart_text": "#334155",
        "chart_title": "#003695",
        "hover_bg": "#FFFFFF",
        "hover_text": "#111827",
        "shadow_sm": "0 1px 2px 0 rgba(15, 23, 42, 0.06)",
        "shadow_md": "0 4px 8px -1px rgba(15, 23, 42, 0.12), 0 2px 4px -1px rgba(15, 23, 42, 0.08)",
        "shadow_lg": "0 10px 15px -3px rgba(15, 23, 42, 0.15), 0 4px 6px -2px rgba(15, 23, 42, 0.1)",
    },
    "dark": {
        "bg_primary": "#0B1220",
        "bg_card": "#111827",
        "bg_sidebar": "#0F172A",
        "text_primary": "#F8FAFC",
        "text_secondary": "#CBD5E1",
        "text_muted": "#94A3B8",
        "border_light": "#334155",
        "border_subtle": "#1F2937",
        "surface_subtle": "#111827",
        "surface_muted": "#1F2937",
        "surface_elevated": "#0F172A",
        "surface_info_soft": "#172554",
        "surface_success_soft": "#052E16",
        "surface_warning_soft": "#451A03",
        "surface_danger_soft": "#450A0A",
        "surface_danger_subtle": "#3F1010",
        "text_success": "#4ADE80",
        "text_warning": "#FBBF24",
        "text_danger": "#FCA5A5",
        "border_success": "#166534",
        "border_warning": "#92400E",
        "border_danger": "#991B1B",
        "plot_bgcolor": "#111827",
        "paper_bgcolor": "#111827",
        "chart_grid": "rgba(148, 163, 184, 0.25)",
        "chart_axis": "#64748B",
        "chart_text": "#E2E8F0",
        "chart_title": "#93C5FD",
        "hover_bg": "#1F2937",
        "hover_text": "#F8FAFC",
        "shadow_sm": "0 1px 2px 0 rgba(2, 6, 23, 0.45)",
        "shadow_md": "0 4px 8px -1px rgba(2, 6, 23, 0.55), 0 2px 4px -1px rgba(2, 6, 23, 0.45)",
        "shadow_lg": "0 10px 15px -3px rgba(2, 6, 23, 0.7), 0 4px 6px -2px rgba(2, 6, 23, 0.55)",
    },
}


def resolve_effective_mode(mode: ThemeMode | None = None) -> ThemeMode:
    """Resolve active theme mode. Dashboard is fixed to light mode."""
    if mode in ("light", "dark"):
        return mode

    return "light"


def get_theme_tokens(mode: ThemeMode | None = None) -> Dict[str, str]:
    """Return merged design tokens for the effective mode."""
    effective = resolve_effective_mode(mode)
    tokens: Dict[str, str] = {}
    tokens.update(COMMON_TOKENS)
    tokens.update(THEME_TOKENS[effective])
    tokens["mode"] = effective
    return tokens


def get_css_variables(mode: ThemeMode | None = None) -> Dict[str, str]:
    """Return CSS variables for global styling."""
    tokens = get_theme_tokens(mode)
    return {
        "--font-sans": tokens["font_family"],
        "--walmart-blue": tokens["walmart_blue"],
        "--walmart-blue-dark": tokens["walmart_blue_dark"],
        "--walmart-blue-light": tokens["walmart_blue_light"],
        "--walmart-yellow": tokens["walmart_yellow"],
        "--color-critical": tokens["color_critical"],
        "--color-warning": tokens["color_warning"],
        "--color-success": tokens["color_success"],
        "--color-info": tokens["color_info"],
        "--bg-primary": tokens["bg_primary"],
        "--bg-card": tokens["bg_card"],
        "--bg-sidebar": tokens["bg_sidebar"],
        "--text-primary": tokens["text_primary"],
        "--text-secondary": tokens["text_secondary"],
        "--text-muted": tokens["text_muted"],
        "--text-success": tokens["text_success"],
        "--text-warning": tokens["text_warning"],
        "--text-danger": tokens["text_danger"],
        "--border-light": tokens["border_light"],
        "--border-subtle": tokens["border_subtle"],
        "--border-success": tokens["border_success"],
        "--border-warning": tokens["border_warning"],
        "--border-danger": tokens["border_danger"],
        "--surface-subtle": tokens["surface_subtle"],
        "--surface-muted": tokens["surface_muted"],
        "--surface-elevated": tokens["surface_elevated"],
        "--surface-info-soft": tokens["surface_info_soft"],
        "--surface-success-soft": tokens["surface_success_soft"],
        "--surface-warning-soft": tokens["surface_warning_soft"],
        "--surface-danger-soft": tokens["surface_danger_soft"],
        "--surface-danger-subtle": tokens["surface_danger_subtle"],
        "--plot-bg": tokens["plot_bgcolor"],
        "--paper-bg": tokens["paper_bgcolor"],
        "--chart-grid": tokens["chart_grid"],
        "--chart-axis": tokens["chart_axis"],
        "--chart-text": tokens["chart_text"],
        "--chart-title": tokens["chart_title"],
        "--hover-bg": tokens["hover_bg"],
        "--hover-text": tokens["hover_text"],
        "--shadow-sm": tokens["shadow_sm"],
        "--shadow-md": tokens["shadow_md"],
        "--shadow-lg": tokens["shadow_lg"],
    }


def build_css_variables_block(mode: ThemeMode | None = None) -> str:
    """Build a CSS block that defines active custom properties."""
    variables = get_css_variables(mode)
    variable_lines = "\n".join([f"  {key}: {value};" for key, value in variables.items()])
    return f":root {{\n{variable_lines}\n}}"


def get_component_colors(mode: ThemeMode | None = None) -> Dict[str, str]:
    """Return backward-compatible color aliases consumed by dashboard pages."""
    tokens = get_theme_tokens(mode)
    return {
        "walmart_blue": tokens["walmart_blue"],
        "walmart_blue_dark": tokens["walmart_blue_dark"],
        "walmart_blue_light": tokens["walmart_blue_light"],
        "walmart_yellow": tokens["walmart_yellow"],
        "background": tokens["bg_primary"],
        "critical": tokens["color_critical"],
        "warning": tokens["color_warning"],
        "success": tokens["color_success"],
        "text_dark": tokens["text_primary"],
        "text_light": tokens["text_secondary"],
        "plot_bg": tokens["plot_bgcolor"],
        "paper_bg": tokens["paper_bgcolor"],
        "font_family": tokens["font_family"],
        "chart_grid": tokens["chart_grid"],
        "chart_axis": tokens["chart_axis"],
        "chart_text": tokens["chart_text"],
        "chart_title": tokens["chart_title"],
        "hover_bg": tokens["hover_bg"],
        "hover_text": tokens["hover_text"],
        "border_light": tokens["border_light"],
        "text_muted": tokens["text_muted"],
    }


def apply_plotly_theme(fig: go.Figure, mode: ThemeMode | None = None) -> go.Figure:
    """Apply consistent Plotly styling while respecting native Streamlit theme."""
    colors = get_component_colors(mode)

    fig.update_layout(
        plot_bgcolor=colors["plot_bg"],
        paper_bgcolor=colors["paper_bg"],
        font=dict(family=colors["font_family"], color=colors["chart_text"]),
        title=dict(font=dict(color=colors["chart_title"])),
        legend=dict(bgcolor="rgba(0, 0, 0, 0)", font=dict(color=colors["chart_text"])),
        hoverlabel=dict(
            bgcolor=colors["hover_bg"],
            font=dict(color=colors["hover_text"], family=colors["font_family"]),
            bordercolor=colors["border_light"],
        ),
    )
    fig.update_xaxes(
        showline=True,
        linecolor=colors["chart_axis"],
        gridcolor=colors["chart_grid"],
        zerolinecolor=colors["chart_grid"],
        tickfont=dict(color=colors["chart_text"]),
        title_font=dict(color=colors["chart_text"]),
    )
    fig.update_yaxes(
        showline=True,
        linecolor=colors["chart_axis"],
        gridcolor=colors["chart_grid"],
        zerolinecolor=colors["chart_grid"],
        tickfont=dict(color=colors["chart_text"]),
        title_font=dict(color=colors["chart_text"]),
    )
    return fig


__all__ = [
    "ThemeMode",
    "resolve_effective_mode",
    "get_theme_tokens",
    "get_css_variables",
    "build_css_variables_block",
    "get_component_colors",
    "apply_plotly_theme",
]

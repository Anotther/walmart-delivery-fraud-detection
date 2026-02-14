"""
Walmart Fraud Detection Dashboard - Reusable Components
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from textwrap import dedent
from typing import Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as st_components

from src.dashboard.theme import (
    apply_plotly_theme,
    build_css_variables_block,
    get_component_colors,
    resolve_effective_mode,
)

# Backward-compatible color dictionary used across page modules.
COLORS: Dict[str, str] = get_component_colors("light")

def _sync_component_colors(theme_mode: str | None = None) -> None:
    """Refresh shared color aliases based on current theme."""
    COLORS.clear()
    COLORS.update(get_component_colors(theme_mode))


def _inject_theme_dom_attributes(effective_mode: str) -> None:
    """Set attributes/classes used by CSS selectors in the main document."""
    st_components.html(
        f"""
        <script>
        (function() {{
          const effectiveMode = "{effective_mode}";

          const applyMode = () => {{
            const appRoot = window.parent?.document || document;
            const targets = [
              appRoot.documentElement,
              appRoot.body,
              ...appRoot.querySelectorAll('.stApp'),
            ];

            targets.forEach((el) => {{
              if (!el) return;
              el.setAttribute('data-dashboard-theme', effectiveMode);
              el.classList.remove('dashboard-theme-light', 'dashboard-theme-dark');
              el.classList.add(effectiveMode === 'dark' ? 'dashboard-theme-dark' : 'dashboard-theme-light');
            }});
          }};

          applyMode();
          setTimeout(applyMode, 50);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def _patch_plotly_chart_renderer() -> None:
    """Patch Streamlit Plotly renderer once to enforce theme on every figure."""
    try:
        from streamlit.delta_generator import DeltaGenerator
    except Exception:
        return

    if getattr(DeltaGenerator, "_dashboard_theme_patch", False):
        return

    original_plotly_chart = DeltaGenerator.plotly_chart

    def themed_plotly_chart(self, figure_or_data=None, *args, **kwargs):
        if isinstance(figure_or_data, go.Figure):
            apply_plotly_theme(figure_or_data)
        return original_plotly_chart(self, figure_or_data, *args, **kwargs)

    DeltaGenerator.plotly_chart = themed_plotly_chart
    DeltaGenerator._dashboard_theme_patch = True


def load_css():
    """
    Inject global CSS and sync visual tokens with Streamlit native theme.
    """
    effective_mode = resolve_effective_mode()
    _sync_component_colors(effective_mode)

    css_path = Path(__file__).parent.parent.parent / "dashboard/styles/main.css"
    with open(css_path, "r", encoding="utf-8") as css_file:
        css_content = css_file.read()

    # Main stylesheet ships default/fallback tokens in :root for bootstrapping.
    # Inject computed theme variables after it so runtime mode wins.
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    st.markdown(
        f"<style>{build_css_variables_block(effective_mode)}</style>",
        unsafe_allow_html=True,
    )

    # Keep Inter as preferred font, with local fallbacks when remote font is blocked.
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap" rel="stylesheet">
        """,
        unsafe_allow_html=True,
    )

    _inject_theme_dom_attributes(effective_mode)
    _patch_plotly_chart_renderer()


def kpi_card(
    title: str,
    value: Union[int, float, str],
    delta: Optional[str] = None,
    delta_color: str = "normal",
    color: Optional[str] = None,
    tooltip: Optional[str] = None,
    card_class: Optional[str] = None,
):
    """Display a custom styled KPI card using CSS classes."""
    if color is None:
        color = COLORS["walmart_blue_light"]

    delta_html = '<div class="kpi-meta"></div>'
    if delta:
        is_pos = str(delta).startswith("+")
        if delta_color == "inverse":
            d_class = "delta-neg" if is_pos else "delta-pos"
        elif delta_color == "normal":
            d_class = "delta-pos" if is_pos else "delta-neg"
        else:
            d_class = "delta-neu"

        delta_html = f'<div class="kpi-meta"><span class="{d_class}">{delta}</span></div>'

    tooltip_attr = f'title="{escape(str(tooltip), quote=True)}"' if tooltip else ""
    info_icon = " ℹ️" if tooltip else ""
    extra_class = f" {card_class.strip()}" if card_class else ""
    cursor_style = "help" if tooltip else "default"

    html_code = f"""
    <div class="kpi-card{extra_class}" style="border-left-color: {color}; cursor: {cursor_style};" {tooltip_attr}>
        <div class="kpi-title">{title}{info_icon}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """
    st.markdown(html_code, unsafe_allow_html=True)


def insight_card(title: str, content: str, icon: str = "💡", compact: bool = False):
    """Display a narrative insight card."""
    classes = "insight-card compact" if compact else "insight-card"
    clean_content = dedent(str(content)).strip()
    st.markdown(
        f"""
    <div class="{classes}">
        <div class="insight-header">
            <span class="insight-title">{icon} {title}</span>
        </div>
        <div class="insight-body">
            {clean_content}
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def plot_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
    key: Optional[str] = None,
):
    """Unified bar chart styling with tooltip support."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        color_discrete_sequence=[
            COLORS["walmart_blue"],
            COLORS["walmart_yellow"],
            COLORS["walmart_blue_light"],
        ],
        hover_data=hover_data,
    )
    fig.update_layout(
        title_font_color=COLORS["walmart_blue"],
        title_font_size=14,
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor=COLORS["chart_grid"], title=None),
        margin=dict(t=40, l=10, r=10, b=10),
        barcornerradius=4,
    )
    fig.update_traces(hovertemplate="%{x}: <b>%{y}</b><extra></extra>")
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


def plot_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    hover_data: Optional[List[str]] = None,
    key: Optional[str] = None,
):
    """Unified line chart styling with tooltip support."""
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        color_discrete_sequence=[COLORS["walmart_blue_light"]],
        hover_data=hover_data,
        markers=True,
        text=y,
    )
    fig.update_traces(
        line=dict(width=3, shape="spline"),
        marker=dict(size=8, symbol="circle"),
        textposition="top center",
        texttemplate="%{y}",
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
    )
    fig.update_layout(
        title_font_color=COLORS["walmart_blue"],
        title_font_size=14,
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=False, title=None, rangemode="tozero"),
        margin=dict(t=40, l=10, r=10, b=10),
        hovermode="x unified",
    )
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


def risk_badge(level: str):
    """Display a colored badge for risk level."""
    color_map = {
        "Critical": COLORS["critical"],
        "High": COLORS["warning"],
        "Medium": COLORS["warning"],
        "Low": COLORS["success"],
    }
    bg_color = color_map.get(level, COLORS["text_light"])

    st.markdown(
        f"""
    <span style="
        background-color: {bg_color};
        color: var(--text-primary);
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        border: 1px solid var(--border-light);
    ">{level}</span>
    """,
        unsafe_allow_html=True,
    )


def plot_dual_axis_trend(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    title: str,
    y1_label: str = None,
    y2_label: str = None,
    key: Optional[str] = None,
):
    """Plot trend with two y-axes for metric comparison."""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df[x],
            y=df[y1],
            name=y1_label or y1,
            marker_color=COLORS["walmart_blue_light"],
            opacity=0.7,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df[x],
            y=df[y2],
            name=y2_label or y2,
            mode="lines+markers",
            marker=dict(size=8, color=COLORS["walmart_yellow"]),
            line=dict(width=3),
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS["walmart_blue"], size=14)),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title=y1_label,
            showgrid=True,
            gridcolor=COLORS["chart_grid"],
        ),
        yaxis2=dict(
            title=y2_label,
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, l=10, r=10, b=10),
        hovermode="x unified",
    )
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


def plot_correlation_heatmap(df: pd.DataFrame, title: str, key: Optional[str] = None):
    """Plot simple correlation heatmap."""
    fig = px.imshow(
        df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS["walmart_blue"], size=14)),
        margin=dict(t=40, l=10, r=10, b=10),
    )
    fig = apply_plotly_theme(fig)
    st.plotly_chart(fig, use_container_width=True, key=key)


def plot_hypothesis_card(
    id: str,
    statement: str,
    status: str,
    result_text: str,
    methodology: str,
    p_value: Optional[float] = None,
    metric_name: Optional[str] = None,
    metric_value: Optional[float] = None,
):
    """Display a styled hypothesis validation card."""
    status_config = {
        "Validated": {"color": COLORS["success"], "icon": "✅"},
        "Rejected": {"color": COLORS["critical"], "icon": "❌"},
        "Investigating": {"color": COLORS["warning"], "icon": "⏳"},
    }
    config = status_config.get(status, {"color": COLORS["text_light"], "icon": "❓"})
    color = config["color"]
    icon = config["icon"]

    p_val_html = ""
    if p_value is not None:
        p_val_html = (
            f'<div style="margin-top:4px; font-size: 0.8rem; color: var(--text-secondary);">'
            f"p-value: <strong>{p_value:.4f}</strong></div>"
        )

    metric_html = ""
    if metric_name and metric_value is not None:
        metric_html = (
            f"<div style=\"background: var(--surface-muted); padding: 8px 12px; border-radius: 6px; "
            f"border: 1px solid var(--border-light); margin-top: 12px;\">"
            f"<div style=\"font-size: 0.75rem; text-transform: uppercase; color: var(--text-secondary); font-weight: 600;\">{metric_name}</div>"
            f"<div style=\"font-size: 1.1rem; font-weight: 700; color: {COLORS['walmart_blue']};\">{metric_value:.2f}</div>{p_val_html}</div>"
        )

    card_html = f"""<div style="background: var(--bg-card); border: 1px solid var(--border-light); border-left: 4px solid {color}; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: var(--shadow-sm);">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
<div style="display: flex; gap: 0.75rem; align-items: center;">
<span style="background: var(--surface-muted); color: var(--text-primary); padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; border: 1px solid var(--border-light);">{id}</span>
<span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary);">Hypothesis</span>
</div>
<div style="background: {color}26; color: {color}; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 0.75rem; border: 1px solid {color}; display: flex; align-items: center; gap: 4px;">{icon} {status.upper()}</div>
</div>
<h4 style="margin: 0 0 1rem 0; font-size: 1.05rem; font-weight: 600; color: var(--text-primary); line-height: 1.4;">{statement}</h4>
<div style="color: var(--text-secondary); font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">{result_text}</div>
{metric_html}
<div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border-light); display: flex; justify-content: space-between; align-items: center;">
<div style="font-size: 0.8rem; color: var(--text-secondary); display: flex; align-items: center; gap: 6px;">
<span>🔬 Method:</span>
<span style="background: var(--surface-info-soft); color: {COLORS['walmart_blue']}; padding: 2px 6px; border-radius: 4px; font-weight: 500;">{methodology}</span>
</div>
</div>
</div>"""

    st.markdown(card_html, unsafe_allow_html=True)


def plot_drift_card(metric_name: str, current_val: float, ref_val: float, status: str):
    """Display model drift status."""
    status_icon = "🟢" if status == "Stable" else "🔴" if status == "Degrading" else "🟡"
    change = ((current_val - ref_val) / ref_val) * 100 if ref_val != 0 else 0
    delta_color = COLORS["critical"] if change > 0 else COLORS["success"]

    st.markdown(
        f"""
    <div style="background: var(--surface-subtle); border-radius: 6px; padding: 1rem; border: 1px solid var(--border-light);">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-size: 0.9rem; font-weight: 500; color: var(--text-secondary);">{metric_name}</span>
            <span>{status_icon}</span>
        </div>
        <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">
            {current_val:.1f}%
            <span style="font-size: 0.8rem; color: {delta_color}; font-weight: normal; margin-left: 0.5rem;">
                {change:+.1f}% vs Ref
            </span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 0.25rem;">
            Baseline: {ref_val:.1f}%
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the standard sidebar content."""
    with st.sidebar:
        st.page_link("app.py", label="Home")
        st.page_link("pages/1_Overview.py", label="Overview")
        st.page_link("pages/2_Monitor.py", label="Monitor")
        st.page_link("pages/3_Drivers.py", label="Drivers")
        st.page_link("pages/4_Customers.py", label="Customers")
        st.page_link("pages/5_Geographic.py", label="Geographic")
        st.page_link("pages/6_Product_Analysis.py", label="Product Analysis")
        st.page_link("pages/8_Patterns.py", label="Patterns")
        st.page_link("pages/7_Methodology.py", label="Methodology")
        st.page_link("pages/9_Model_Performance.py", label="Model Performance")

        st.markdown("---")
        st.caption(f"Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
        st.caption("Owner: Fraud Ops Team")
        st.caption("Walmart Inc. © 2024")

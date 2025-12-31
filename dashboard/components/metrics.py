"""
Metric card components for the dashboard.
"""
import streamlit as st
from typing import Optional, Union
import pandas as pd


def metric_card(
    label: str,
    value: Union[int, float, str],
    delta: Optional[Union[int, float, str]] = None,
    delta_color: str = "normal",
    help_text: Optional[str] = None
):
    """
    Create a metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional change/delta value
        delta_color: 'normal', 'inverse', or 'off'
        help_text: Optional tooltip text
    """
    st.metric(
        label=label,
        value=value,
        delta=delta,
        delta_color=delta_color,
        help=help_text
    )


def metric_row(metrics: list, columns: int = 4):
    """
    Create a row of metrics.

    Args:
        metrics: List of dicts with label, value, delta, etc.
        columns: Number of columns
    """
    cols = st.columns(columns)

    for i, metric in enumerate(metrics):
        with cols[i % columns]:
            metric_card(
                label=metric.get("label", ""),
                value=metric.get("value", ""),
                delta=metric.get("delta"),
                delta_color=metric.get("delta_color", "normal"),
                help_text=metric.get("help")
            )


def kpi_card(
    title: str,
    value: Union[int, float, str],
    subtitle: Optional[str] = None,
    icon: str = "📊",
    color: str = "#0071ce"
):
    """
    Create a styled KPI card with HTML.

    Args:
        title: Card title
        value: Main value
        subtitle: Optional subtitle
        icon: Emoji icon
        color: Accent color
    """
    subtitle_html = f'<p style="font-size: 0.9rem; color: #666; margin: 0;">{subtitle}</p>' if subtitle else ""

    st.markdown(f"""
    <div style="
        background-color: #f8f9fa;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 1rem;
    ">
        <p style="font-size: 0.9rem; color: #666; margin: 0 0 0.5rem 0;">{icon} {title}</p>
        <p style="font-size: 1.8rem; font-weight: bold; color: #1a1a1a; margin: 0;">{value}</p>
        {subtitle_html}
    </div>
    """, unsafe_allow_html=True)


def summary_stats(df: pd.DataFrame, columns: list):
    """
    Display summary statistics for selected columns.

    Args:
        df: DataFrame
        columns: Columns to summarize
    """
    stats = df[columns].describe()

    st.dataframe(
        stats.style.format("{:.2f}"),
        use_container_width=True
    )


def comparison_metric(
    label: str,
    current: float,
    previous: float,
    format_str: str = "{:.2f}",
    higher_is_better: bool = False
):
    """
    Create a comparison metric showing change.

    Args:
        label: Metric label
        current: Current value
        previous: Previous value
        format_str: Format string for values
        higher_is_better: Whether higher values are better
    """
    if previous != 0:
        change = ((current - previous) / previous) * 100
    else:
        change = 0

    delta_str = f"{change:+.1f}%"

    # Determine delta color
    if change > 0:
        delta_color = "normal" if higher_is_better else "inverse"
    elif change < 0:
        delta_color = "inverse" if higher_is_better else "normal"
    else:
        delta_color = "off"

    st.metric(
        label=label,
        value=format_str.format(current),
        delta=delta_str,
        delta_color=delta_color
    )


def risk_indicator(
    score: float,
    entity_name: str,
    show_score: bool = True
):
    """
    Display a risk indicator with color coding.

    Args:
        score: Risk score (0-100)
        entity_name: Name of the entity
        show_score: Whether to show the numeric score
    """
    if score < 25:
        color = "#28a745"
        level = "Low Risk"
    elif score < 50:
        color = "#ffc107"
        level = "Medium Risk"
    elif score < 75:
        color = "#fd7e14"
        level = "High Risk"
    else:
        color = "#dc3545"
        level = "Critical"

    score_text = f" ({score:.0f})" if show_score else ""

    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        padding: 0.5rem;
        background-color: #f8f9fa;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    ">
        <div style="
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background-color: {color};
            margin-right: 0.5rem;
        "></div>
        <span style="flex-grow: 1;">{entity_name}</span>
        <span style="color: {color}; font-weight: bold;">{level}{score_text}</span>
    </div>
    """, unsafe_allow_html=True)


def progress_metric(
    label: str,
    current: float,
    target: float,
    format_str: str = "{:.0f}"
):
    """
    Display a progress metric toward a target.

    Args:
        label: Metric label
        current: Current value
        target: Target value
        format_str: Format string
    """
    progress = min(current / target, 1.0) if target > 0 else 0

    st.markdown(f"**{label}**")
    st.progress(progress)
    st.markdown(f"{format_str.format(current)} / {format_str.format(target)}")

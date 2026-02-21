"""
Reusable chart components for the dashboard.
"""
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional, List


def create_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    orientation: str = "v",
    color_scale: str = "Blues"
) -> go.Figure:
    """Create a bar chart."""
    fig = px.bar(
        df,
        x=x,
        y=y,
        title=title,
        color=color or y,
        orientation=orientation,
        color_continuous_scale=color_scale
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    markers: bool = True
) -> go.Figure:
    """Create a line chart."""
    fig = px.line(
        df,
        x=x,
        y=y,
        title=title,
        markers=markers
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_pie_chart(
    df: pd.DataFrame,
    values: str,
    names: str,
    title: str,
    hole: float = 0.3
) -> go.Figure:
    """Create a donut/pie chart."""
    fig = px.pie(
        df,
        values=values,
        names=names,
        title=title,
        hole=hole
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_scatter_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    size: Optional[str] = None,
    hover_data: Optional[List[str]] = None
) -> go.Figure:
    """Create a scatter chart."""
    fig = px.scatter(
        df,
        x=x,
        y=y,
        title=title,
        color=color,
        size=size,
        hover_data=hover_data
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_histogram(
    df: pd.DataFrame,
    x: str,
    title: str,
    nbins: int = 30,
    color: Optional[str] = None
) -> go.Figure:
    """Create a histogram."""
    fig = px.histogram(
        df,
        x=x,
        title=title,
        nbins=nbins,
        color=color
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_box_plot(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None
) -> go.Figure:
    """Create a box plot."""
    fig = px.box(
        df,
        x=x,
        y=y,
        title=title,
        color=color
    )
    fig.update_layout(
        template="plotly_white",
        height=400
    )
    return fig


def create_heatmap(
    df: pd.DataFrame,
    title: str,
    color_scale: str = "RdBu_r"
) -> go.Figure:
    """Create a heatmap."""
    fig = px.imshow(
        df,
        title=title,
        color_continuous_scale=color_scale,
        text_auto=".2f"
    )
    fig.update_layout(
        template="plotly_white",
        height=500
    )
    return fig


def create_dual_axis_chart(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    title: str,
    y1_name: str = "Primary",
    y2_name: str = "Secondary"
) -> go.Figure:
    """Create a chart with two y-axes."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(x=df[x], y=df[y1], name=y1_name),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(x=df[x], y=df[y2], name=y2_name, mode="lines+markers"),
        secondary_y=True,
    )

    fig.update_layout(
        title=title,
        template="plotly_white",
        height=400
    )

    fig.update_yaxes(title_text=y1_name, secondary_y=False)
    fig.update_yaxes(title_text=y2_name, secondary_y=True)

    return fig


def create_gauge_chart(
    value: float,
    title: str,
    max_value: float = 100,
    thresholds: Optional[dict] = None
) -> go.Figure:
    """Create a gauge chart."""
    if thresholds is None:
        thresholds = {
            "low": 25,
            "medium": 50,
            "high": 75
        }

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        gauge={
            "axis": {"range": [0, max_value]},
            "bar": {"color": "darkblue"},
            "steps": [
                {"range": [0, thresholds["low"]], "color": "lightgreen"},
                {"range": [thresholds["low"], thresholds["medium"]], "color": "yellow"},
                {"range": [thresholds["medium"], thresholds["high"]], "color": "orange"},
                {"range": [thresholds["high"], max_value], "color": "red"},
            ],
        }
    ))

    fig.update_layout(height=300)
    return fig


def create_treemap(
    df: pd.DataFrame,
    path: List[str],
    values: str,
    title: str,
    color: Optional[str] = None
) -> go.Figure:
    """Create a treemap."""
    fig = px.treemap(
        df,
        path=path,
        values=values,
        title=title,
        color=color
    )
    fig.update_layout(height=500)
    return fig

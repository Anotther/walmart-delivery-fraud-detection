"""
Walmart Fraud Detection Dashboard - Reusable Components
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Union, Optional, List, Dict
from pathlib import Path
from textwrap import dedent
from html import escape

# Color Palette
COLORS = {
    "walmart_blue": "#004c91",
    "walmart_blue_dark": "#003695",
    "walmart_blue_light": "#0071ce",
    "walmart_yellow": "#ffc220",
    "background": "#F9FAFB",
    "critical": "#EF4444",
    "warning": "#F59E0B",
    "success": "#10B981",
    "text_dark": "#1F2937",
    "text_light": "#6B7280"
}

def load_css():
    """Inject global CSS from styles/main.css."""
    css_path = Path(__file__).parent.parent.parent / "dashboard/styles/main.css"
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    # Inject Inter Font from Google Fonts
    st.markdown("""
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap" rel="stylesheet">
    """, unsafe_allow_html=True)

def kpi_card(
    title: str,
    value: Union[int, float, str],
    delta: Optional[str] = None,
    delta_color: str = "normal",
    color: str = "#0071ce", # Default Walmart Light Blue
    tooltip: Optional[str] = None,
    card_class: Optional[str] = None,
):
    """
    Display a custom styled KPI card using CSS classes.
    """
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
    st.markdown(f"""
    <div class="{classes}">
        <div class="insight-header">
            <span class="insight-title">{icon} {title}</span>
        </div>
        <div class="insight-body">
            {clean_content}
        </div>
    </div>
    """, unsafe_allow_html=True)

def plot_bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: Optional[str] = None,
    hover_data: Optional[List[str]] = None,
    key: Optional[str] = None
):
    """Unified bar chart styling with tooltip support."""
    fig = px.bar(
        df, x=x, y=y, title=title,
        color=color,
        color_discrete_sequence=[COLORS['walmart_blue'], COLORS['walmart_yellow'], COLORS['walmart_blue_light']],
        hover_data=hover_data
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter",
        title_font_color=COLORS['walmart_blue'],
        title_font_size=14,
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=True, gridcolor='#f3f4f6', title=None),
        margin=dict(t=40, l=10, r=10, b=10),
        barcornerradius=4
    )
    # Minimalist hover
    fig.update_traces(hovertemplate='%{x}: <b>%{y}</b><extra></extra>')
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_line_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    hover_data: Optional[List[str]] = None,
    key: Optional[str] = None
):
    """Unified line chart styling with tooltip support."""
    fig = px.line(
        df, x=x, y=y, title=title,
        color_discrete_sequence=[COLORS['walmart_blue_light']],
        hover_data=hover_data,
        markers=True,
        text=y  # Enable data labels
    )
    fig.update_traces(
        line=dict(width=3, shape='spline'), 
        marker=dict(size=8, symbol='circle'),
        textposition="top center", # Position labels
        texttemplate='%{y}',       # Format labels
        hovertemplate='%{x}: <b>%{y}</b><extra></extra>'
    )
    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter",
        title_font_color=COLORS['walmart_blue'],
        title_font_size=14,
        xaxis=dict(showgrid=False, title=None),
        yaxis=dict(showgrid=False, title=None, rangemode="tozero"), # Clean grid, start at 0
        margin=dict(t=40, l=10, r=10, b=10),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

def risk_badge(level: str):
    """Display a colored badge for risk level."""
    color_map = {
        "Critical": COLORS['critical'],
        "High": COLORS['warning'],
        "Medium": COLORS['warning'],
        "Low": COLORS['success']
    }
    bg_color = color_map.get(level, "#ccc")
    
    st.markdown(f"""
    <span style="
        background-color: {bg_color};
        color: white;
        padding: 0.2rem 0.6rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: bold;
    ">{level}</span>
    """, unsafe_allow_html=True)

def plot_dual_axis_trend(
    df: pd.DataFrame,
    x: str,
    y1: str,
    y2: str,
    title: str,
    y1_label: str = None,
    y2_label: str = None,
    key: Optional[str] = None
):
    """Plot trend with two y-axes for metric comparison."""
    fig = go.Figure()

    # Bar Chart (Primary Axis)
    fig.add_trace(go.Bar(
        x=df[x],
        y=df[y1],
        name=y1_label or y1,
        marker_color=COLORS['walmart_blue_light'],
        opacity=0.7
    ))

    # Line Chart (Secondary Axis)
    fig.add_trace(go.Scatter(
        x=df[x],
        y=df[y2],
        name=y2_label or y2,
        mode='lines+markers',
        marker=dict(size=8, color=COLORS['walmart_yellow']),
        line=dict(width=3),
        yaxis='y2'
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS['walmart_blue'], size=14, family="Inter")),
        xaxis=dict(showgrid=False),
        yaxis=dict(
            title=y1_label, 
            showgrid=True, 
            gridcolor='#f3f4f6'
        ),
        yaxis2=dict(
            title=y2_label,
            overlaying='y',
            side='right',
            showgrid=False
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=50, l=10, r=10, b=10),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_correlation_heatmap(df: pd.DataFrame, title: str, key: Optional[str] = None):
    """Plot simple correlation heatmap."""
    fig = px.imshow(
        df,
        text_auto=".2f",
        aspect="auto",
        color_continuous_scale="RdBu_r",
        zmin=-1, zmax=1
    )
    fig.update_layout(
        title=dict(text=title, font=dict(color=COLORS['walmart_blue'], size=14, family="Inter")),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font_family="Inter",
        margin=dict(t=40, l=10, r=10, b=10)
    )
    st.plotly_chart(fig, use_container_width=True, key=key)

def plot_hypothesis_card(
    id: str,
    statement: str, 
    status: str, 
    result_text: str,
    methodology: str,
    p_value: Optional[float] = None,
    metric_name: Optional[str] = None,
    metric_value: Optional[float] = None
):
    """Display a styled hypothesis validation card."""
    status_config = {
        "Validated": {"color": COLORS['success'], "icon": "✅"},
        "Rejected": {"color": COLORS['critical'], "icon": "❌"},
        "Investigating": {"color": COLORS['warning'], "icon": "⏳"}
    }
    config = status_config.get(status, {"color": "#6b7280", "icon": "❓"})
    color = config['color']
    icon = config['icon']
    
    # Build p-value HTML
    p_val_html = ""
    if p_value is not None:
        p_val_html = f'<div style="margin-top:4px; font-size: 0.8rem; color: #6b7280;">p-value: <strong>{p_value:.4f}</strong></div>'
    
    # Build metric HTML
    metric_html = ""
    if metric_name and metric_value is not None:
        metric_html = f'''<div style="background: {COLORS['background']}; padding: 8px 12px; border-radius: 6px; border: 1px solid #e5e7eb; margin-top: 12px;"><div style="font-size: 0.75rem; text-transform: uppercase; color: #6b7280; font-weight: 600;">{metric_name}</div><div style="font-size: 1.1rem; font-weight: 700; color: {COLORS['walmart_blue']};">{metric_value:.2f}</div>{p_val_html}</div>'''

    # Card HTML - all styles inline on single lines
    card_html = f'''<div style="background: white; border: 1px solid #e5e7eb; border-left: 4px solid {color}; border-radius: 8px; padding: 1.25rem; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
<div style="display: flex; gap: 0.75rem; align-items: center;">
<span style="background: #f3f4f6; color: #374151; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 0.8rem; border: 1px solid #d1d5db;">{id}</span>
<span style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #6b7280;">Hypothesis</span>
</div>
<div style="background: {color}15; color: {color}; padding: 4px 10px; border-radius: 999px; font-weight: 700; font-size: 0.75rem; border: 1px solid {color}30; display: flex; align-items: center; gap: 4px;">{icon} {status.upper()}</div>
</div>
<h4 style="margin: 0 0 1rem 0; font-size: 1.05rem; font-weight: 600; color: #111827; line-height: 1.4;">{statement}</h4>
<div style="color: #4b5563; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">{result_text}</div>
{metric_html}
<div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid #f3f4f6; display: flex; justify-content: space-between; align-items: center;">
<div style="font-size: 0.8rem; color: #6b7280; display: flex; align-items: center; gap: 6px;">
<span>🔬 Method:</span>
<span style="background: #eef2ff; color: {COLORS['walmart_blue']}; padding: 2px 6px; border-radius: 4px; font-weight: 500;">{methodology}</span>
</div>
</div>
</div>'''
    
    st.markdown(card_html, unsafe_allow_html=True)

def plot_drift_card(metric_name: str, current_val: float, ref_val: float, status: str):
    """Display model drift status."""
    status_icon = "🟢" if status == "Stable" else "🔴" if status == "Degrading" else "🟡"
    change = ((current_val - ref_val) / ref_val) * 100 if ref_val != 0 else 0
    
    st.markdown(f"""
    <div style="background: #f9fafb; border-radius: 6px; padding: 1rem; border: 1px solid #e5e7eb;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="font-size: 0.9rem; font-weight: 500; color: #4b5563;">{metric_name}</span>
            <span>{status_icon}</span>
        </div>
        <div style="font-size: 1.25rem; font-weight: 700; color: #1f2937;">
            {current_val:.1f}%
            <span style="font-size: 0.8rem; color: {'#ef4444' if change > 0 else '#10b981'}; font-weight: normal; margin-left: 0.5rem;">
                {change:+.1f}% vs Ref
            </span>
        </div>
        <div style="font-size: 0.8rem; color: #9ca3af; margin-top: 0.25rem;">
            Baseline: {ref_val:.1f}%
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Render the standard sidebar content."""
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/Walmart_logo.svg", width=150)
        st.markdown("### Navigation")
        # Pages are automatically listed by Streamlit
        
        st.info("System Status: Online 🟢")
        
        # Governance Headers (Dashboard Playbook)
        st.markdown("---")
        st.caption("Last Updated")
        st.markdown(f"**{pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}**")
        
        st.caption("Owner")
        st.markdown("**Fraud Ops Team**")
        
        st.markdown("---")
        st.caption("Walmart Inc. © 2024")

"""
Visualization Theme Module - Walmart Fraud Detection Project

This module provides standardized color palettes, fonts, and styling
for all visualizations across notebooks and dashboards.

Usage:
    from src.config.viz_theme import PROJECT_THEME, REGION_COLORS, get_highlight_colors

    # Apply risk colors
    color_discrete_map=PROJECT_THEME['risk_colors']

    # Get highlight colors for bar charts
    colors = get_highlight_colors(data, highlight_index=0)
"""

from typing import List, Dict, Any, Optional
import plotly.io as pio
import plotly.graph_objects as go


# =============================================================================
# PROJECT THEME - Global Configuration
# =============================================================================

PROJECT_THEME = {
    # Mode and fonts
    'mode': 'light',
    'font_family': 'DejaVu Sans, Arial, sans-serif',

    # Font sizes
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'annotation_size': 11,

    # Grid and layout
    'grid_alpha': 0.25,
    'line_width': 2.0,
    'marker_size': 6,
    'default_height': 400,
    'default_width': 800,

    # Core brand colors (Walmart)
    'walmart_blue': '#0071CE',
    'walmart_yellow': '#FFC220',
    'primary': '#0071CE',  # Primary color for general use (Walmart blue)

    # Risk category colors (FIXED STANDARD - use across all notebooks)
    'risk_colors': {
        'Low': '#28A745',       # Green - safe
        'Medium': '#FFC107',    # Yellow - caution
        'High': '#FD7E14',      # Orange - warning
        'Critical': '#DC3545'   # Red - danger
    },

    # Risk order for sorting
    'risk_order': ['Critical', 'High', 'Medium', 'Low'],
    'risk_order_asc': ['Low', 'Medium', 'High', 'Critical'],

    # Fraud-specific colors
    'fraud_red': '#E74C3C',
    'safe_green': '#2ECC71',
    'neutral_gray': '#4A4A4A',
    'light_gray': '#95A5A6',
    'highlight_orange': '#E69F00',
    'highlight_blue': '#0072B2',

    # Binary comparison colors
    'binary_colors': {
        'positive': '#E74C3C',   # Has fraud/missing
        'negative': '#2ECC71',   # No fraud/complete
    },

    # Categorical palette (colorblind-safe - Okabe-Ito)
    'categorical': [
        '#0072B2',  # Blue
        '#E69F00',  # Orange
        '#009E73',  # Green
        '#D55E00',  # Vermillion
        '#CC79A7',  # Pink
        '#56B4E9',  # Sky blue
        '#F0E442',  # Yellow
        '#999999',  # Gray
    ],

    # Sequential colormaps (for magnitude)
    'sequential_blue': 'Blues',
    'sequential_red': 'Reds',
    'sequential_orange': 'Oranges',
    'sequential_green': 'Greens',

    # Divergent colormaps (for +/- or above/below average)
    'divergent': 'RdBu_r',
    'divergent_green_red': 'RdYlGn_r',

    # Background colors
    'plot_bgcolor': 'rgba(248, 249, 250, 0.5)',
    'paper_bgcolor': 'white',
}


# =============================================================================
# REGION COLORS - Consistent mapping for Central Florida regions
# =============================================================================

REGION_COLORS = {
    'Altamonte Springs': '#E69F00',  # Orange (highlight if highest risk)
    'Apopka': '#56B4E9',             # Sky blue
    'Clermont': '#009E73',           # Green
    'Kissimmee': '#0072B2',          # Blue
    'Orlando': '#CC79A7',            # Pink
    'Sanford': '#D55E00',            # Vermillion
    'Winter Park': '#F0E442',        # Yellow
}


# =============================================================================
# PRICE SEGMENT COLORS
# =============================================================================

PRICE_SEGMENT_COLORS = {
    'Budget': '#28A745',      # Green - low value
    'Mid-Range': '#FFC107',   # Yellow - medium value
    'Premium': '#FD7E14',     # Orange - high value
    'Luxury': '#DC3545',      # Red - highest value
}


# =============================================================================
# CATEGORY COLORS - Product categories
# =============================================================================

CATEGORY_COLORS = {
    'Electronics': '#0072B2',
    'Clothing': '#E69F00',
    'Food': '#009E73',
    'Home & Garden': '#D55E00',
    'Health & Beauty': '#CC79A7',
    'Sports': '#56B4E9',
    'Toys': '#F0E442',
    'Automotive': '#999999',
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_highlight_colors(
    data: List,
    highlight_index: int,
    neutral: str = None,
    highlight: str = None
) -> List[str]:
    """
    Returns a list of colors with highlight for a specific index.

    Args:
        data: List or array-like object to get length from
        highlight_index: Index to highlight (use -1 for last item)
        neutral: Color for non-highlighted items (default: neutral_gray)
        highlight: Color for highlighted item (default: highlight_orange)

    Returns:
        List of color strings

    Example:
        >>> colors = get_highlight_colors(df, highlight_index=-1)
        >>> fig = px.bar(..., color=colors, color_discrete_map="identity")
    """
    if neutral is None:
        neutral = PROJECT_THEME['neutral_gray']
    if highlight is None:
        highlight = PROJECT_THEME['highlight_orange']

    n = len(data)
    if highlight_index < 0:
        highlight_index = n + highlight_index

    colors = [neutral] * n
    if 0 <= highlight_index < n:
        colors[highlight_index] = highlight

    return colors


def get_top_n_highlight_colors(
    data: List,
    top_n: int = 1,
    neutral: str = None,
    highlight: str = None,
    ascending: bool = False
) -> List[str]:
    """
    Returns colors highlighting the top N items (assuming data is sorted).

    Args:
        data: List or array-like object
        top_n: Number of items to highlight
        neutral: Color for non-highlighted items
        highlight: Color for highlighted items
        ascending: If True, highlight first N; if False, highlight last N

    Returns:
        List of color strings
    """
    if neutral is None:
        neutral = PROJECT_THEME['neutral_gray']
    if highlight is None:
        highlight = PROJECT_THEME['fraud_red']

    n = len(data)
    colors = [neutral] * n

    if ascending:
        for i in range(min(top_n, n)):
            colors[i] = highlight
    else:
        for i in range(max(0, n - top_n), n):
            colors[i] = highlight

    return colors


def get_risk_color(risk_category: str) -> str:
    """
    Get the standard color for a risk category.

    Args:
        risk_category: One of 'Low', 'Medium', 'High', 'Critical'

    Returns:
        Hex color string
    """
    return PROJECT_THEME['risk_colors'].get(risk_category, PROJECT_THEME['neutral_gray'])


def apply_project_theme(fig: go.Figure) -> go.Figure:
    """
    Apply the project's standard theme to a Plotly figure.

    Args:
        fig: Plotly figure object

    Returns:
        Modified figure with theme applied
    """
    fig.update_layout(
        font_family=PROJECT_THEME['font_family'],
        title_font_size=PROJECT_THEME['title_size'],
        font_size=PROJECT_THEME['label_size'],
        plot_bgcolor=PROJECT_THEME['plot_bgcolor'],
        paper_bgcolor=PROJECT_THEME['paper_bgcolor'],
        hoverlabel=dict(
            bgcolor="white",
            font_size=PROJECT_THEME['tick_size'],
            font_family=PROJECT_THEME['font_family']
        ),
    )

    # Update axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        tickfont_size=PROJECT_THEME['tick_size'],
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128, 128, 128, 0.2)',
        tickfont_size=PROJECT_THEME['tick_size'],
    )

    return fig


def create_gauge_chart(
    value: float,
    title: str,
    max_value: float = 100,
    thresholds: Dict[str, float] = None,
    suffix: str = '%'
) -> go.Figure:
    """
    Create a standardized gauge chart with risk-based coloring.

    Args:
        value: Current value to display
        title: Chart title
        max_value: Maximum value for the gauge
        thresholds: Dict with 'low', 'medium', 'high' threshold values
        suffix: Suffix for the value display (e.g., '%', '$')

    Returns:
        Plotly Figure object
    """
    if thresholds is None:
        thresholds = {
            'low': RiskThresholds.MEDIUM,
            'medium': RiskThresholds.HIGH,
            'high': RiskThresholds.CRITICAL
        }

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title, 'font': {'size': PROJECT_THEME['title_size']}},
        number={'suffix': suffix, 'font': {'size': 24}},
        gauge={
            'axis': {'range': [0, max_value], 'tickwidth': 1},
            'bar': {'color': PROJECT_THEME['walmart_blue']},
            'steps': [
                {'range': [0, thresholds['low']], 'color': PROJECT_THEME['risk_colors']['Low']},
                {'range': [thresholds['low'], thresholds['medium']], 'color': PROJECT_THEME['risk_colors']['Medium']},
                {'range': [thresholds['medium'], thresholds['high']], 'color': PROJECT_THEME['risk_colors']['High']},
                {'range': [thresholds['high'], max_value], 'color': PROJECT_THEME['risk_colors']['Critical']},
            ],
            'threshold': {
                'line': {'color': "black", 'width': 2},
                'thickness': 0.75,
                'value': value
            }
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20),
        font_family=PROJECT_THEME['font_family'],
    )

    return fig


# =============================================================================
# AXIS LABELS WITH UNITS - Standard labels for common metrics
# =============================================================================

AXIS_LABELS = {
    'missing_rate': 'Taxa de Itens Faltantes (%)',
    'missing_rate_en': 'Missing Rate (%)',
    'order_amount': 'Valor do Pedido (US$)',
    'order_amount_en': 'Order Amount ($)',
    'value_lost': 'Valor Perdido (US$)',
    'value_lost_en': 'Value Lost ($)',
    'total_orders': 'Total de Pedidos',
    'total_orders_en': 'Total Orders',
    'risk_score': 'Score de Risco (0-100)',
    'risk_score_en': 'Risk Score (0-100)',
    'count': 'Quantidade',
    'count_en': 'Count',
    'frequency': 'Frequência',
    'frequency_en': 'Frequency',
    'price': 'Preço (US$)',
    'price_en': 'Price ($)',
    'times_missing': 'Vezes Reportado Faltante',
    'times_missing_en': 'Times Reported Missing',
}


def get_label(key: str, lang: str = 'en') -> str:
    """
    Get standardized axis label with units.

    Args:
        key: Label key (e.g., 'missing_rate', 'order_amount')
        lang: Language ('en' for English, 'pt' for Portuguese)

    Returns:
        Formatted label string with units
    """
    if lang == 'pt':
        return AXIS_LABELS.get(key, key)
    else:
        return AXIS_LABELS.get(f'{key}_en', AXIS_LABELS.get(key, key))


# =============================================================================
# PLOTLY TEMPLATE REGISTRATION
# =============================================================================

def register_project_template():
    """
    Register a custom Plotly template for the project.

    Usage:
        from src.config.viz_theme import register_project_template
        register_project_template()

        # Then in your plots:
        fig.update_layout(template='walmart_fraud')
    """
    template = go.layout.Template()

    template.layout = go.Layout(
        font=dict(
            family=PROJECT_THEME['font_family'],
            size=PROJECT_THEME['label_size'],
        ),
        title=dict(
            font=dict(size=PROJECT_THEME['title_size']),
            x=0.5,
            xanchor='center',
        ),
        plot_bgcolor=PROJECT_THEME['plot_bgcolor'],
        paper_bgcolor=PROJECT_THEME['paper_bgcolor'],
        colorway=PROJECT_THEME['categorical'],
        hoverlabel=dict(
            bgcolor="white",
            font_size=PROJECT_THEME['tick_size'],
        ),
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
        ),
    )

    pio.templates['walmart_fraud'] = template


# Register template on import
try:
    register_project_template()
except Exception:
    pass  # Ignore if Plotly not fully loaded

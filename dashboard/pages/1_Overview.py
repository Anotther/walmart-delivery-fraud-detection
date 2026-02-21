"""
Walmart Fraud Detection Dashboard - Executive Overview
Enhanced version with business context and actionable insights
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.express as px

# Add src to path - use resolve() to follow symlinks
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.dashboard.components import (
    load_css,
    kpi_card,
    plot_line_chart,
    COLORS,
    render_sidebar,
    risk_badge
)
from src.dashboard.data_cache import get_default_cache, reset_default_cache

st.set_page_config(
    page_title="Executive Overview - Walmart Fraud Detection",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Global CSS
load_css()

def get_data_source_version():
    """Get a version string for cache invalidation based on data source type."""
    from src.data_source import get_data_source
    ds = get_data_source()
    # Include data availability in version to invalidate cache if source changes
    return f"{ds.source_type}_{ds.is_available()}"


def ensure_fresh_cache():
    """Reset cache if needed to ensure fresh data."""
    from src.data_source import get_data_source
    ds = get_data_source()

    # Check if we need to reset the cache
    # This happens when the data source type changes or becomes unavailable
    cache = get_default_cache()

    # If cache's data source type doesn't match current, reset it
    if hasattr(cache, '_data_source') and cache._data_source.source_type != ds.source_type:
        reset_default_cache()


@st.cache_data(ttl=900, show_spinner="Loading dashboard data...")
def get_dashboard_data(_source_version: str):
    """
    Fetch all necessary data for the overview page using lazy loading.
    This method loads only the data required for the Overview page,
    reducing load time and memory footprint.

    Args:
        _source_version: Cache version key (from get_data_source_version())
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for this page
    page_data = cache.get_page_data('overview')

    # Check for errors in page_data
    error_keys = [k for k in page_data.keys() if k.endswith('_error')]
    if error_keys:
        errors = {k: page_data[k] for k in error_keys}
        st.error(f"Error loading page data: {errors}")
        st.stop()

    # Extract required datasets from page data with error handling
    required_keys = ['overview_metrics', 'temporal_trends', 'risk_distribution', 'top_suspicious']
    missing_keys = [k for k in required_keys if k not in page_data]
    if missing_keys:
        st.error(f"Missing required data keys: {missing_keys}")
        st.error(f"Available keys: {list(page_data.keys())}")
        st.stop()

    metrics = page_data['overview_metrics']
    trends = page_data['temporal_trends']
    # Re-fetch alerts with specific threshold (page_data uses default threshold)
    alerts = cache.get_risk_alerts(threshold=70)
    regional = cache.get_regional_summary()
    risk_dist = page_data['risk_distribution']
    top_suspicious = page_data['top_suspicious']

    return metrics, trends, alerts, regional, risk_dist, top_suspicious

def calculate_business_impact(metrics):
    """Calculate business impact metrics from data."""
    # National context: $6.5B losses in 2023, 53% from e-commerce ($3.445B)
    # Central Florida is one pilot region
    national_ecommerce_loss = 6_500_000_000 * 0.53  # $3.445 billion

    # Calculate projected annual impact for Central Florida
    estimated_annual_loss = metrics['estimated_loss'] * 12  # Assuming monthly data

    # Calculate what percentage reduction would mean
    target_reduction = 0.25  # 25% reduction target
    potential_savings = estimated_annual_loss * target_reduction

    return {
        'national_context': national_ecommerce_loss,
        'projected_annual_loss': estimated_annual_loss,
        'potential_savings': potential_savings,
        'target_reduction_pct': target_reduction * 100
    }

def calculate_trend_delta(monthly_df):
    """Calculate month-over-month change in missing rate."""
    if len(monthly_df) < 2:
        return 0.0, "stable"

    current = monthly_df.iloc[-1]['missing_rate']
    previous = monthly_df.iloc[-2]['missing_rate']
    delta = current - previous

    direction = "up" if delta > 0.5 else "down" if delta < -0.5 else "stable"
    return delta, direction

def main():
    # Sidebar
    render_sidebar()

    # Ensure cache is fresh (reset if data source changed)
    ensure_fresh_cache()

    # Load Data with cache invalidation based on data source
    source_version = get_data_source_version()
    metrics, trends, alerts, regional, risk_dist, top_suspicious = get_dashboard_data(source_version)
    business_impact = calculate_business_impact(metrics)
    delta_missing, trend_direction = calculate_trend_delta(trends['monthly'])

    # ============================================================================
    # HEADER: Executive Context (Original Layout)
    # ============================================================================
    st.markdown("### Overview")
    st.markdown(f"""
    <div class="dashboard-header-row">
        <div>
            <h1 style="margin:0; font-size: 2.5rem;">Network Health Monitor</h1>
            <p class="text-muted">Analysis of delivery anomalies in Central Florida Region.</p>
        </div>
        <div class="scope-badge-container">
             <span class="badge badge-warning">High Alert Level</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption(f"Data Period: {metrics['date_range_start']} to {metrics['date_range_end']}")

    # ============================================================================
    # SECTION 1: Executive KPIs - The Critical Numbers
    # ============================================================================
    st.markdown("### Executive Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        # Orders Analyzed with real trend
        orders_delta = f"+{metrics['total_orders']:,}" if metrics['total_orders'] > 0 else "No data"
        kpi_card(
            "Orders Analyzed (YTD)",
            f"{metrics['total_orders']:,}",
            delta=f"{metrics['date_range_start']} to {metrics['date_range_end']}",
            delta_color="normal",
            color=COLORS['walmart_blue'],
            tooltip="Total delivery orders processed in Central Florida region for fraud analysis"
        )

    with col2:
        # Missing Rate with trend direction
        rate = metrics['overall_missing_rate']
        delta_symbol = "↑" if delta_missing > 0 else "↓" if delta_missing < 0 else "→"
        delta_text = f"{delta_symbol} {abs(delta_missing):.2f}% MoM"

        kpi_card(
            "Missing Item Rate",
            f"{rate:.2f}%",
            delta=delta_text,
            delta_color="inverse",  # Higher is worse
            color=COLORS['critical'] if rate > 10.0 else COLORS['warning'] if rate > 5.0 else COLORS['success'],
            tooltip="Percentage of items reported missing vs. total items ordered. National e-commerce average: ~2-3%"
        )

    with col3:
        # Financial Impact with context
        loss = business_impact['projected_annual_loss']
        kpi_card(
            "Projected Annual Loss",
            f"${loss:,.0f}",
            delta=f"${business_impact['potential_savings']:,.0f} recoverable at 25% reduction",
            delta_color="normal",
            color=COLORS['critical'],
            tooltip="Estimated financial impact extrapolated to full year based on current missing item rate"
        )

    with col4:
        # High-Risk Alerts
        critical_alerts = len(alerts[alerts['risk_category'] == 'Critical']) if len(alerts) > 0 else 0
        high_alerts = len(alerts[alerts['risk_category'] == 'High']) if len(alerts) > 0 else 0

        kpi_card(
            "Critical Alerts",
            f"{critical_alerts}",
            delta=f"+{high_alerts} High priority",
            delta_color="inverse",
            color=COLORS['critical'],
            tooltip="Entities (drivers/customers/regions) flagged for immediate investigation"
        )

    # ============================================================================
    # SECTION 2: Risk Intelligence Summary
    # ============================================================================
    st.markdown("---")
    st.markdown("### Risk Intelligence Summary")

    col_risk1, col_risk2, col_risk3 = st.columns(3)

    with col_risk1:
        # Driver Risk Distribution
        driver_dist = risk_dist['driver_risk_distribution']
        critical_drivers = driver_dist.get('Critical', 0)
        high_drivers = driver_dist.get('High', 0)

        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {COLORS['warning']};">
            <div class="kpi-title">Driver Risk Profile</div>
            <div class="kpi-value" style="color: {COLORS['critical']};">{critical_drivers}</div>
            <div class="kpi-meta">
                <span style="color: {COLORS['text_dark']};">Critical Risk Drivers</span><br>
                <span style="font-size: 0.85rem; color: {COLORS['text_light']};">
                    +{high_drivers} High Risk | {driver_dist.get('Medium', 0)} Medium
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_risk2:
        # Customer Risk Distribution
        customer_dist = risk_dist['customer_risk_distribution']
        critical_customers = customer_dist.get('Critical', 0)
        high_customers = customer_dist.get('High', 0)

        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {COLORS['warning']};">
            <div class="kpi-title">Customer Risk Profile</div>
            <div class="kpi-value" style="color: {COLORS['critical']};">{critical_customers}</div>
            <div class="kpi-meta">
                <span style="color: {COLORS['text_dark']};">Critical Risk Customers</span><br>
                <span style="font-size: 0.85rem; color: {COLORS['text_light']};">
                    +{high_customers} High Risk | {customer_dist.get('Medium', 0)} Medium
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_risk3:
        # Orders with Issues
        flagged_orders = metrics['orders_with_missing']
        flagged_pct = metrics['pct_orders_with_missing']

        st.markdown(f"""
        <div class="kpi-card" style="border-left-color: {COLORS['walmart_blue_light']};">
            <div class="kpi-title">Flagged Orders</div>
            <div class="kpi-value">{flagged_pct:.1f}%</div>
            <div class="kpi-meta">
                <span style="color: {COLORS['text_dark']};">{flagged_orders:,} orders with missing items</span><br>
                <span style="font-size: 0.85rem; color: {COLORS['text_light']};">
                    Out of {metrics['total_orders']:,} total orders
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ============================================================================
    # SECTION 3: Trends & Patterns
    # ============================================================================
    st.markdown("---")
    st.markdown("### Fraud Trends & Patterns")
    st.caption(
        "This section explains how missing-rate behavior evolves over time and where trend pressure is increasing or easing. "
        "Use it to validate whether recent operational actions are reducing risk."
    )

    monthly_df = trends['monthly']
    avg_rate = monthly_df['missing_rate'].mean() if len(monthly_df) > 0 else 0

    if len(monthly_df) >= 2:
        current_month = monthly_df.iloc[-1]
        prev_month = monthly_df.iloc[-2]
        mom_change = current_month['missing_rate'] - prev_month['missing_rate']
        mom_pct = (mom_change / prev_month['missing_rate'] * 100) if prev_month['missing_rate'] > 0 else 0
        mom_text = f"{mom_change:+.2f} pp"
        mom_caption = f"{mom_pct:+.1f}% vs {prev_month['month_name']}"
        mom_color = COLORS['success'] if mom_change < 0 else COLORS['critical']
    else:
        mom_text = "N/A"
        mom_caption = "Insufficient history"
        mom_color = COLORS['text_light']

    if len(monthly_df) > 0:
        peak_month = monthly_df.loc[monthly_df['missing_rate'].idxmax()]
        peak_text = f"{peak_month['month_name']} {peak_month['missing_rate']:.2f}%"
    else:
        peak_text = "N/A"

    def stat_card(title: str, value: str, caption: str, color: str) -> None:
        st.markdown(
            f"""
            <div style="padding: 0.85rem; background: {COLORS['background']}; border-radius: 6px; margin-bottom: 0.8rem;
                        border-left: 4px solid {color};">
                <div style="font-size: 0.8rem; color: {COLORS['text_light']}; text-transform: uppercase; letter-spacing: 0.04em;">
                    {title}
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {COLORS['text_dark']};">
                    {value}
                </div>
                <div style="font-size: 0.85rem; color: {COLORS['text_light']};">
                    {caption}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    col_trend_left, col_trend_right = st.columns([1, 3])

    with col_trend_left:
        st.markdown("#### Trend Indicators")
        stat_card("MoM Change", mom_text, mom_caption, mom_color)
        stat_card("Annual Average", f"{avg_rate:.2f}%", "Missing item rate", COLORS['walmart_blue'])
        stat_card("Peak Month", peak_text, "Highest rate", COLORS['walmart_yellow'])

    with col_trend_right:
        if len(monthly_df) > 0:
            plot_line_chart(
                monthly_df,
                x="month_name",
                y="missing_rate",
                title="Monthly Missing Item Rate - 12 Month Analysis",
                hover_data=["orders", "items_missing"]
            )

    # ============================================================================
    # SECTION 4: Geographic Hotspots
    # ============================================================================
    st.markdown("---")
    st.markdown("### Geographic Intelligence")
    st.caption(
        "This section highlights where risk is concentrated across regions. "
        "Use it to prioritize geographic investigations and local mitigation plans."
    )

    if not regional.empty and len(regional) > 0:
        regional_sorted = regional.sort_values("missing_rate", ascending=False).head(5).copy()
        avg_regional_rate = regional['missing_rate'].mean()
        regional_sorted["risk_level"] = np.where(
            regional_sorted["missing_rate"] > avg_regional_rate * 1.5,
            "Critical",
            np.where(
                regional_sorted["missing_rate"] > avg_regional_rate * 1.2,
                "High",
                np.where(regional_sorted["missing_rate"] > avg_regional_rate, "Medium", "Low"),
            ),
        )
        regional_sorted["rate_label"] = regional_sorted["missing_rate"].map(lambda value: f"{value:.2f}%")

        col_geo_left, col_geo_right = st.columns([1, 3])

        with col_geo_left:
            st.markdown("#### Regional Breakdown")

            for _, row in regional_sorted.iterrows():
                risk_level = row["risk_level"]

                risk_color = COLORS['critical'] if risk_level == 'Critical' else \
                            COLORS['warning'] if risk_level == 'High' else \
                            COLORS['walmart_yellow'] if risk_level == 'Medium' else COLORS['success']

                st.markdown(
                    f"""
                    <div style="padding: 0.75rem; background: {COLORS['background']};
                                border-left: 3px solid {risk_color}; margin-bottom: 0.5rem; border-radius: 4px;">
                        <div style="font-weight: bold; color: {COLORS['text_dark']};">
                            {row['region']}
                        </div>
                        <div style="font-size: 0.85rem; color: {COLORS['text_light']}; margin-top: 0.25rem;">
                            Rate: {row['missing_rate']:.2f}% | Orders: {row['total_orders']:.0f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        with col_geo_right:
            fig_regions = px.bar(
                regional_sorted,
                x="region",
                y="missing_rate",
                title="Top 5 High-Risk Regions - Fraud Concentration Analysis",
                color="risk_level",
                color_discrete_map={
                    "Critical": COLORS["critical"],
                    "High": COLORS["warning"],
                    "Medium": COLORS["walmart_yellow"],
                    "Low": COLORS["success"],
                },
                category_orders={"risk_level": ["Critical", "High", "Medium", "Low"]},
                text="rate_label",
                custom_data=["items_missing", "total_orders", "risk_level"],
            )
            fig_regions.update_traces(
                textposition="outside",
                cliponaxis=False,
                hovertemplate=(
                    "Region: %{x}<br>"
                    "Missing Rate: %{y:.2f}%<br>"
                    "Items Missing: %{customdata[0]:,.0f}<br>"
                    "Orders: %{customdata[1]:,.0f}<br>"
                    "Risk Level: %{customdata[2]}"
                    "<extra></extra>"
                ),
            )
            fig_regions.update_layout(
                xaxis_title=None,
                yaxis_title="Missing Rate (%)",
                margin=dict(t=45, l=10, r=10, b=10),
                legend_title_text="Risk Level",
            )
            st.plotly_chart(fig_regions, use_container_width=True)

if __name__ == "__main__":
    main()

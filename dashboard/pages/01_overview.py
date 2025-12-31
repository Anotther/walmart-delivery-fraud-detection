"""
Overview Page - Key metrics and summary dashboard.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.aggregations import get_overall_statistics
from src.analysis.temporal import analyze_monthly_trends, analyze_day_of_week_patterns
from src.analysis.geographic import analyze_regional_performance


st.set_page_config(page_title="Overview - Walmart Fraud Detection", page_icon="📊", layout="wide")

st.title("📊 Overview Dashboard")
st.markdown("Key metrics and trends for Walmart e-commerce fraud detection.")


@st.cache_data(ttl=3600)
def load_data():
    """Load and cache data."""
    raw_data = extract_all()
    data = transform_all(raw_data)
    return data


try:
    with st.spinner("Loading data..."):
        data = load_data()
        orders = data["orders"]
        drivers = data["drivers"]
        customers = data["customers"]

        stats = get_overall_statistics(orders, drivers, customers)

    # Key Metrics
    st.markdown("## Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Orders", f"{stats['total_orders']:,}")

    with col2:
        st.metric("Total Revenue", f"${stats['total_revenue']:,.0f}")

    with col3:
        st.metric("Overall Missing Rate", f"{stats['overall_missing_rate']:.2f}%")

    with col4:
        st.metric("Orders with Issues", f"{stats['orders_with_missing']:,}")

    st.markdown("---")

    # Monthly Trends
    st.markdown("## Monthly Trends")

    monthly = analyze_monthly_trends(orders)
    monthly["month"] = monthly["month"].astype(str)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            monthly,
            x="month",
            y="total_orders",
            title="Orders per Month",
            labels={"month": "Month", "total_orders": "Orders"}
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(
            monthly,
            x="month",
            y="missing_rate",
            title="Missing Rate Trend",
            labels={"month": "Month", "missing_rate": "Missing Rate (%)"},
            markers=True
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Regional Analysis
    st.markdown("## Regional Performance")

    regional = analyze_regional_performance(orders)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            regional.sort_values("missing_rate", ascending=True),
            x="missing_rate",
            y="region",
            orientation="h",
            title="Missing Rate by Region",
            labels={"missing_rate": "Missing Rate (%)", "region": "Region"},
            color="missing_rate",
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.pie(
            regional,
            values="total_orders",
            names="region",
            title="Orders Distribution by Region",
            hole=0.4
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Day of Week Patterns
    st.markdown("## Day of Week Patterns")

    daily = analyze_day_of_week_patterns(orders)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(
            daily,
            x="day_of_week",
            y="total_orders",
            title="Orders by Day of Week",
            labels={"day_of_week": "Day", "total_orders": "Orders"},
            color="is_weekend",
            color_discrete_map={True: "orange", False: "blue"}
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.bar(
            daily,
            x="day_of_week",
            y="missing_rate",
            title="Missing Rate by Day of Week",
            labels={"day_of_week": "Day", "missing_rate": "Missing Rate (%)"},
            color="missing_rate",
            color_continuous_scale="Reds"
        )
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Quick Stats Table
    st.markdown("## Summary Statistics")

    summary_df = pd.DataFrame({
        "Metric": [
            "Total Orders", "Total Revenue", "Average Order Value",
            "Total Items Delivered", "Total Items Missing", "Missing Rate",
            "Active Drivers", "Active Customers", "Regions"
        ],
        "Value": [
            f"{stats['total_orders']:,}",
            f"${stats['total_revenue']:,.2f}",
            f"${stats['avg_order_value']:.2f}",
            f"{stats['total_items_delivered']:,}",
            f"{stats['total_items_missing']:,}",
            f"{stats['overall_missing_rate']:.2f}%",
            f"{stats['active_drivers']}",
            f"{stats['active_customers']}",
            f"{stats['total_regions']}"
        ]
    })

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.dataframe(summary_df, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.info("Please ensure data files are in the 'data/' directory.")

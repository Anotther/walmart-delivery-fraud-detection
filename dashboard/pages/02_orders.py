"""
Orders Page - Order analysis and patterns.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_orders
from src.etl.transformers import transform_orders
from src.features.order_features import create_order_features, get_high_risk_orders


st.set_page_config(page_title="Orders - Walmart Fraud Detection", page_icon="📦", layout="wide")

st.title("📦 Orders Analysis")
st.markdown("Analyze order patterns and identify high-risk deliveries.")


@st.cache_data(ttl=3600)
def load_orders():
    """Load and process orders data."""
    raw = extract_orders()
    transformed = transform_orders(raw)
    featured = create_order_features(transformed)
    return featured


try:
    with st.spinner("Loading orders..."):
        orders = load_orders()

    # Filters
    st.sidebar.markdown("### Filters")

    # Date filter
    orders["order_date"] = pd.to_datetime(orders["order_date"])
    min_date = orders["order_date"].min().date()
    max_date = orders["order_date"].max().date()

    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Region filter
    regions = st.sidebar.multiselect(
        "Regions",
        options=sorted(orders["region"].unique()),
        default=sorted(orders["region"].unique())
    )

    # Apply filters
    filtered = orders[
        (orders["order_date"].dt.date >= date_range[0]) &
        (orders["order_date"].dt.date <= date_range[1]) &
        (orders["region"].isin(regions))
    ]

    st.markdown(f"**Showing {len(filtered):,} orders**")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Orders", f"{len(filtered):,}")

    with col2:
        st.metric("Total Revenue", f"${filtered['order_amount'].sum():,.0f}")

    with col3:
        total_items = filtered["items_delivered"].sum() + filtered["items_missing"].sum()
        missing_rate = filtered["items_missing"].sum() / total_items * 100 if total_items > 0 else 0
        st.metric("Missing Rate", f"{missing_rate:.2f}%")

    with col4:
        orders_with_missing = (filtered["items_missing"] > 0).sum()
        st.metric("Orders with Issues", f"{orders_with_missing:,}")

    st.markdown("---")

    # Visualizations
    tab1, tab2, tab3 = st.tabs(["Distribution", "Patterns", "High Risk"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                filtered,
                x="order_amount",
                nbins=30,
                title="Order Amount Distribution",
                labels={"order_amount": "Order Amount ($)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.histogram(
                filtered,
                x="total_items",
                nbins=20,
                title="Items per Order Distribution",
                labels={"total_items": "Total Items"}
            )
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                filtered[filtered["has_missing"]],
                x="items_missing",
                title="Missing Items Distribution (Orders with Issues)",
                labels={"items_missing": "Items Missing"}
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(
                filtered,
                names="has_missing",
                title="Orders with Missing Items",
                color_discrete_map={True: "red", False: "green"}
            )
            fig.update_traces(labels=["No Issues", "Has Issues"])
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            # By region
            regional = filtered.groupby("region").agg({
                "order_id": "count",
                "items_missing": "sum",
                "items_delivered": "sum"
            }).reset_index()
            regional["missing_rate"] = regional["items_missing"] / (regional["items_delivered"] + regional["items_missing"]) * 100

            fig = px.bar(
                regional.sort_values("missing_rate", ascending=False),
                x="region",
                y="missing_rate",
                title="Missing Rate by Region",
                labels={"region": "Region", "missing_rate": "Missing Rate (%)"},
                color="missing_rate",
                color_continuous_scale="Reds"
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # By order size
            size_stats = filtered.groupby("order_size").agg({
                "order_id": "count",
                "missing_rate": "mean"
            }).reset_index()
            size_stats.columns = ["order_size", "count", "avg_missing_rate"]

            fig = px.bar(
                size_stats,
                x="order_size",
                y="avg_missing_rate",
                title="Missing Rate by Order Size",
                labels={"order_size": "Order Size", "avg_missing_rate": "Avg Missing Rate (%)"},
                color="avg_missing_rate",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Delivery period
        period_stats = filtered.groupby("delivery_period").agg({
            "order_id": "count",
            "items_missing": "sum",
            "items_delivered": "sum"
        }).reset_index()
        period_stats["missing_rate"] = period_stats["items_missing"] / (period_stats["items_delivered"] + period_stats["items_missing"]) * 100

        fig = px.bar(
            period_stats,
            x="delivery_period",
            y=["order_id", "missing_rate"],
            title="Orders and Missing Rate by Delivery Period",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### High Risk Orders")

        risk_threshold = st.slider(
            "Minimum Missing Rate (%)",
            min_value=0,
            max_value=100,
            value=50
        )

        high_risk = get_high_risk_orders(filtered, missing_rate_threshold=risk_threshold)

        st.markdown(f"**Found {len(high_risk):,} high-risk orders**")

        if len(high_risk) > 0:
            display_cols = [
                "order_id", "order_date", "region", "order_amount",
                "items_delivered", "items_missing", "missing_rate",
                "driver_id", "customer_id"
            ]
            display_cols = [c for c in display_cols if c in high_risk.columns]

            st.dataframe(
                high_risk[display_cols].head(100),
                hide_index=True,
                use_container_width=True
            )

            # Download button
            csv = high_risk.to_csv(index=False)
            st.download_button(
                label="Download High Risk Orders",
                data=csv,
                file_name="high_risk_orders.csv",
                mime="text/csv"
            )
        else:
            st.info("No high-risk orders found with current filters.")

except Exception as e:
    st.error(f"Error: {str(e)}")

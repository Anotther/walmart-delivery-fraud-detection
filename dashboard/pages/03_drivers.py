"""
Drivers Page - Driver performance analysis.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.driver_features import create_driver_features, get_suspicious_drivers, get_driver_risk_scores


st.set_page_config(page_title="Drivers - Walmart Fraud Detection", page_icon="🚗", layout="wide")

st.title("🚗 Driver Analysis")
st.markdown("Analyze driver performance and identify suspicious patterns.")


@st.cache_data(ttl=3600)
def load_data():
    """Load and process data."""
    raw_data = extract_all()
    data = transform_all(raw_data)
    orders = data["orders"]
    drivers = data["drivers"]
    driver_features = create_driver_features(drivers, orders)
    return driver_features, orders


try:
    with st.spinner("Loading driver data..."):
        driver_features, orders = load_data()
        driver_risk = get_driver_risk_scores(driver_features)

    # Filters
    st.sidebar.markdown("### Filters")

    min_orders = st.sidebar.slider(
        "Minimum Orders",
        min_value=0,
        max_value=int(driver_features["total_orders"].max()),
        value=1
    )

    age_groups = st.sidebar.multiselect(
        "Age Groups",
        options=driver_features["age_group"].dropna().unique().tolist(),
        default=driver_features["age_group"].dropna().unique().tolist()
    )

    # Apply filters
    filtered = driver_risk[
        (driver_risk["total_orders"] >= min_orders) &
        (driver_risk["age_group"].isin(age_groups))
    ]

    st.markdown(f"**Showing {len(filtered):,} drivers**")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Drivers", f"{len(filtered):,}")

    with col2:
        st.metric("Avg Missing Rate", f"{filtered['missing_rate'].mean():.2f}%")

    with col3:
        high_risk = (filtered["risk_category"] == "High") | (filtered["risk_category"] == "Critical")
        st.metric("High Risk Drivers", f"{high_risk.sum():,}")

    with col4:
        st.metric("Total Deliveries", f"{filtered['total_orders'].sum():,}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Risk Analysis", "Suspicious Drivers"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                filtered,
                x="missing_rate",
                nbins=30,
                title="Missing Rate Distribution",
                labels={"missing_rate": "Missing Rate (%)"}
            )
            fig.add_vline(
                x=filtered["missing_rate"].mean(),
                line_dash="dash",
                line_color="red",
                annotation_text="Average"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.histogram(
                filtered,
                x="total_orders",
                nbins=20,
                title="Orders per Driver Distribution",
                labels={"total_orders": "Total Orders"}
            )
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            # By age group
            age_stats = filtered.groupby("age_group").agg({
                "driver_id": "count",
                "missing_rate": "mean"
            }).reset_index()
            age_stats.columns = ["age_group", "count", "avg_missing_rate"]

            fig = px.bar(
                age_stats,
                x="age_group",
                y="avg_missing_rate",
                title="Average Missing Rate by Age Group",
                labels={"age_group": "Age Group", "avg_missing_rate": "Avg Missing Rate (%)"},
                color="avg_missing_rate",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # By experience level
            exp_stats = filtered.groupby("experience_level").agg({
                "driver_id": "count",
                "missing_rate": "mean"
            }).reset_index()
            exp_stats.columns = ["experience_level", "count", "avg_missing_rate"]

            fig = px.bar(
                exp_stats,
                x="experience_level",
                y="avg_missing_rate",
                title="Average Missing Rate by Experience",
                labels={"experience_level": "Experience Level", "avg_missing_rate": "Avg Missing Rate (%)"},
                color="avg_missing_rate",
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        col1, col2 = st.columns(2)

        with col1:
            fig = px.histogram(
                filtered,
                x="risk_score",
                color="risk_category",
                title="Risk Score Distribution",
                labels={"risk_score": "Risk Score", "risk_category": "Category"},
                color_discrete_map={
                    "Low": "green",
                    "Medium": "yellow",
                    "High": "orange",
                    "Critical": "red"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            risk_counts = filtered["risk_category"].value_counts()
            fig = px.pie(
                values=risk_counts.values,
                names=risk_counts.index,
                title="Risk Category Distribution",
                color=risk_counts.index,
                color_discrete_map={
                    "Low": "green",
                    "Medium": "yellow",
                    "High": "orange",
                    "Critical": "red"
                }
            )
            st.plotly_chart(fig, use_container_width=True)

        # Scatter plot
        fig = px.scatter(
            filtered,
            x="total_orders",
            y="missing_rate",
            color="risk_category",
            size="total_items_missing",
            hover_data=["driver_name", "age"],
            title="Missing Rate vs Total Orders",
            labels={
                "total_orders": "Total Orders",
                "missing_rate": "Missing Rate (%)",
                "risk_category": "Risk"
            },
            color_discrete_map={
                "Low": "green",
                "Medium": "yellow",
                "High": "orange",
                "Critical": "red"
            }
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.markdown("### Suspicious Drivers")

        threshold = st.slider(
            "Missing Rate Threshold (%)",
            min_value=0.0,
            max_value=50.0,
            value=15.0
        )

        suspicious = get_suspicious_drivers(filtered, missing_rate_threshold=threshold, min_orders=min_orders)

        st.markdown(f"**Found {len(suspicious):,} suspicious drivers**")

        if len(suspicious) > 0:
            display_cols = [
                "driver_id", "driver_name", "age", "trips",
                "total_orders", "total_items_missing", "missing_rate",
                "pct_orders_with_missing", "risk_score", "risk_category"
            ]
            display_cols = [c for c in display_cols if c in suspicious.columns]

            st.dataframe(
                suspicious[display_cols].head(50),
                hide_index=True,
                use_container_width=True
            )

            csv = suspicious.to_csv(index=False)
            st.download_button(
                label="Download Suspicious Drivers",
                data=csv,
                file_name="suspicious_drivers.csv",
                mime="text/csv"
            )
        else:
            st.info("No suspicious drivers found with current filters.")

except Exception as e:
    st.error(f"Error: {str(e)}")

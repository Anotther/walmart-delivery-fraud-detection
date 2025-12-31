"""
Customers Page - Customer behavior analysis.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.customer_features import create_customer_features, get_suspicious_customers, get_customer_risk_scores


st.set_page_config(page_title="Customers - Walmart Fraud Detection", page_icon="👥", layout="wide")

st.title("👥 Customer Analysis")
st.markdown("Analyze customer behavior and identify suspicious patterns.")


@st.cache_data(ttl=3600)
def load_data():
    """Load and process data."""
    raw_data = extract_all()
    data = transform_all(raw_data)
    orders = data["orders"]
    customers = data["customers"]
    customer_features = create_customer_features(customers, orders)
    return customer_features, orders


try:
    with st.spinner("Loading customer data..."):
        customer_features, orders = load_data()
        customer_risk = get_customer_risk_scores(customer_features)

    # Filter to customers with orders
    active_customers = customer_risk[customer_risk["total_orders"] > 0]

    # Filters
    st.sidebar.markdown("### Filters")

    min_orders = st.sidebar.slider(
        "Minimum Orders",
        min_value=1,
        max_value=int(active_customers["total_orders"].max()),
        value=1
    )

    segments = st.sidebar.multiselect(
        "Customer Segments",
        options=active_customers["customer_segment"].dropna().unique().tolist(),
        default=active_customers["customer_segment"].dropna().unique().tolist()
    )

    # Apply filters
    filtered = active_customers[
        (active_customers["total_orders"] >= min_orders) &
        (active_customers["customer_segment"].isin(segments))
    ]

    st.markdown(f"**Showing {len(filtered):,} customers**")

    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Customers", f"{len(filtered):,}")

    with col2:
        st.metric("Avg Missing Rate", f"{filtered['missing_rate'].mean():.2f}%")

    with col3:
        high_risk = (filtered["risk_category"] == "High") | (filtered["risk_category"] == "Critical")
        st.metric("High Risk Customers", f"{high_risk.sum():,}")

    with col4:
        st.metric("Total Spent", f"${filtered['total_spent'].sum():,.0f}")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Overview", "Risk Analysis", "Suspicious Customers"])

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
                x="total_spent",
                nbins=30,
                title="Total Spending Distribution",
                labels={"total_spent": "Total Spent ($)"}
            )
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            # By age group
            age_stats = filtered.groupby("age_group").agg({
                "customer_id": "count",
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
            # By segment
            seg_stats = filtered.groupby("customer_segment").agg({
                "customer_id": "count",
                "missing_rate": "mean"
            }).reset_index()
            seg_stats.columns = ["segment", "count", "avg_missing_rate"]

            fig = px.bar(
                seg_stats,
                x="segment",
                y="avg_missing_rate",
                title="Average Missing Rate by Segment",
                labels={"segment": "Segment", "avg_missing_rate": "Avg Missing Rate (%)"},
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
            x="total_spent",
            y="missing_rate",
            color="risk_category",
            size="orders_with_missing",
            hover_data=["customer_name", "customer_age"],
            title="Missing Rate vs Total Spending",
            labels={
                "total_spent": "Total Spent ($)",
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
        st.markdown("### Suspicious Customers")

        threshold = st.slider(
            "Missing Rate Threshold (%)",
            min_value=0.0,
            max_value=50.0,
            value=25.0
        )

        suspicious = get_suspicious_customers(filtered, missing_rate_threshold=threshold, min_orders=min_orders)

        st.markdown(f"**Found {len(suspicious):,} suspicious customers**")

        if len(suspicious) > 0:
            display_cols = [
                "customer_id", "customer_name", "customer_age",
                "total_orders", "total_spent", "orders_with_missing",
                "missing_rate", "pct_orders_with_missing", "risk_score", "risk_category"
            ]
            display_cols = [c for c in display_cols if c in suspicious.columns]

            st.dataframe(
                suspicious[display_cols].head(50),
                hide_index=True,
                use_container_width=True
            )

            csv = suspicious.to_csv(index=False)
            st.download_button(
                label="Download Suspicious Customers",
                data=csv,
                file_name="suspicious_customers.csv",
                mime="text/csv"
            )
        else:
            st.info("No suspicious customers found with current filters.")

except Exception as e:
    st.error(f"Error: {str(e)}")

"""
Fraud Detection Page - Risk scoring and anomaly detection.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_all
from src.etl.transformers import transform_all
from src.features.driver_features import create_driver_features
from src.features.customer_features import create_customer_features
from src.features.aggregations import create_driver_customer_matrix
from src.analysis.fraud_patterns import analyze_all_fraud_patterns, generate_fraud_report


st.set_page_config(page_title="Fraud Detection - Walmart Fraud Detection", page_icon="🎯", layout="wide")

st.title("🎯 Fraud Detection")
st.markdown("Risk scoring, anomaly detection, and fraud pattern analysis.")


@st.cache_data(ttl=3600)
def load_data():
    """Load and process data."""
    raw_data = extract_all()
    data = transform_all(raw_data)
    return data


try:
    with st.spinner("Loading data and running fraud detection..."):
        data = load_data()
        orders = data["orders"]
        drivers = data["drivers"]
        customers = data["customers"]

        # Create features
        driver_features = create_driver_features(drivers, orders)
        customer_features = create_customer_features(customers, orders)

        # Run fraud detection
        fraud_indicators = analyze_all_fraud_patterns(orders, drivers, customers)
        fraud_report = generate_fraud_report(fraud_indicators)

        # Get driver-customer interactions
        interactions, suspicious_pairs = create_driver_customer_matrix(orders)

    # Summary metrics
    st.markdown("## Fraud Detection Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Indicators", fraud_report["summary"]["total_indicators"])

    with col2:
        st.metric("High Risk", len(fraud_report["high_risk"]), delta_color="inverse")

    with col3:
        st.metric("Medium Risk", len(fraud_report["medium_risk"]))

    with col4:
        st.metric("Low Risk", len(fraud_report["low_risk"]))

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["High Risk Entities", "Drivers", "Customers", "Collusion"])

    with tab1:
        st.markdown("### High Risk Entities")

        if fraud_report["high_risk"]:
            high_risk_df = pd.DataFrame(fraud_report["high_risk"])

            # Summary by entity type
            col1, col2 = st.columns(2)

            with col1:
                type_counts = high_risk_df["entity_type"].value_counts()
                fig = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    title="High Risk by Entity Type"
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.histogram(
                    high_risk_df,
                    x="score",
                    nbins=20,
                    title="Risk Score Distribution (High Risk)",
                    labels={"score": "Risk Score"}
                )
                st.plotly_chart(fig, use_container_width=True)

            # Table
            st.markdown("#### High Risk Entities List")
            display_df = high_risk_df[["entity_type", "entity_id", "indicator", "score"]].copy()
            display_df["score"] = display_df["score"].round(2)
            st.dataframe(display_df, hide_index=True, use_container_width=True)

            csv = high_risk_df.to_csv(index=False)
            st.download_button(
                label="Download High Risk Report",
                data=csv,
                file_name="high_risk_entities.csv",
                mime="text/csv"
            )
        else:
            st.success("No high-risk entities detected!")

    with tab2:
        st.markdown("### Driver Risk Analysis")

        # Get driver indicators
        driver_indicators = fraud_indicators.get("driver_patterns", [])

        if driver_indicators:
            driver_df = pd.DataFrame([{
                "driver_id": ind.entity_id,
                "score": ind.score,
                "missing_rate_anomaly": ind.details.get("missing_rate_anomaly", {}).get("value", 0),
            } for ind in driver_indicators])

            # Merge with driver info
            driver_risk = driver_df.merge(
                driver_features[["driver_id", "driver_name", "age", "total_orders", "missing_rate"]],
                on="driver_id",
                how="left"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Suspicious Drivers", len(driver_risk))

            with col2:
                st.metric("Avg Risk Score", f"{driver_risk['score'].mean():.1f}")

            # Scatter plot
            fig = px.scatter(
                driver_risk,
                x="total_orders",
                y="missing_rate",
                size="score",
                color="score",
                hover_data=["driver_name"],
                title="Suspicious Drivers: Orders vs Missing Rate",
                labels={"total_orders": "Total Orders", "missing_rate": "Missing Rate (%)"},
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

            # Table
            st.dataframe(
                driver_risk.sort_values("score", ascending=False).head(20),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No suspicious driver patterns detected.")

    with tab3:
        st.markdown("### Customer Risk Analysis")

        customer_indicators = fraud_indicators.get("customer_patterns", [])

        if customer_indicators:
            customer_df = pd.DataFrame([{
                "customer_id": ind.entity_id,
                "score": ind.score,
            } for ind in customer_indicators])

            # Merge with customer info
            customer_risk = customer_df.merge(
                customer_features[["customer_id", "customer_name", "customer_age", "total_orders", "missing_rate", "total_spent"]],
                on="customer_id",
                how="left"
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric("Suspicious Customers", len(customer_risk))

            with col2:
                st.metric("Avg Risk Score", f"{customer_risk['score'].mean():.1f}")

            # Scatter plot
            fig = px.scatter(
                customer_risk,
                x="total_spent",
                y="missing_rate",
                size="score",
                color="score",
                hover_data=["customer_name"],
                title="Suspicious Customers: Spending vs Missing Rate",
                labels={"total_spent": "Total Spent ($)", "missing_rate": "Missing Rate (%)"},
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                customer_risk.sort_values("score", ascending=False).head(20),
                hide_index=True,
                use_container_width=True
            )
        else:
            st.info("No suspicious customer patterns detected.")

    with tab4:
        st.markdown("### Potential Collusion Detection")
        st.markdown("Driver-customer pairs with unusually high missing rates.")

        collusion_indicators = fraud_indicators.get("collusion_patterns", [])

        if collusion_indicators:
            collusion_df = pd.DataFrame([{
                "driver_id": ind.details.get("driver_id"),
                "customer_id": ind.details.get("customer_id"),
                "interactions": ind.details.get("interactions"),
                "missing_rate": ind.details.get("missing_rate"),
                "items_missing": ind.details.get("items_missing"),
                "risk_score": ind.score
            } for ind in collusion_indicators])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Suspicious Pairs", len(collusion_df))

            with col2:
                st.metric("Avg Interactions", f"{collusion_df['interactions'].mean():.1f}")

            with col3:
                st.metric("Avg Missing Rate", f"{collusion_df['missing_rate'].mean():.1f}%")

            # Scatter plot
            fig = px.scatter(
                collusion_df,
                x="interactions",
                y="missing_rate",
                size="items_missing",
                color="risk_score",
                hover_data=["driver_id", "customer_id"],
                title="Suspicious Pairs: Interactions vs Missing Rate",
                labels={"interactions": "Number of Interactions", "missing_rate": "Missing Rate (%)"},
                color_continuous_scale="Reds"
            )
            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(
                collusion_df.sort_values("risk_score", ascending=False),
                hide_index=True,
                use_container_width=True
            )

            csv = collusion_df.to_csv(index=False)
            st.download_button(
                label="Download Collusion Report",
                data=csv,
                file_name="potential_collusion.csv",
                mime="text/csv"
            )
        else:
            st.success("No potential collusion patterns detected!")

except Exception as e:
    st.error(f"Error: {str(e)}")

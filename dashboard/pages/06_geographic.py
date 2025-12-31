"""
Geographic Page - Regional analysis.
"""
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import plotly.express as px

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.etl.extractors import extract_orders
from src.etl.transformers import transform_orders
from src.analysis.geographic import (
    analyze_regional_performance,
    compare_regions,
    identify_regional_hotspots,
    get_regional_summary
)


st.set_page_config(page_title="Geographic - Walmart Fraud Detection", page_icon="🗺️", layout="wide")

st.title("🗺️ Geographic Analysis")
st.markdown("Analyze fraud patterns across different regions in Central Florida.")


@st.cache_data(ttl=3600)
def load_data():
    """Load and process orders data."""
    raw = extract_orders()
    transformed = transform_orders(raw)
    return transformed


try:
    with st.spinner("Loading regional data..."):
        orders = load_data()
        regional = analyze_regional_performance(orders)
        summary = get_regional_summary(orders)
        hotspots = identify_regional_hotspots(orders)

    # Summary metrics
    st.markdown("## Regional Overview")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Regions", summary["total_regions"])

    with col2:
        avg_rate = summary["statistics"]["avg_missing_rate"]
        st.metric("Avg Missing Rate", f"{avg_rate:.2f}%")

    with col3:
        worst = summary["worst_performing"][0] if summary["worst_performing"] else {"region": "N/A"}
        st.metric("Highest Risk Region", worst["region"])

    with col4:
        best = summary["best_performing"][0] if summary["best_performing"] else {"region": "N/A"}
        st.metric("Best Region", best["region"])

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3 = st.tabs(["Performance", "Comparison", "Hotspots"])

    with tab1:
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
            fig.add_vline(
                x=avg_rate,
                line_dash="dash",
                line_color="blue",
                annotation_text="Average"
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                regional.sort_values("total_orders", ascending=True),
                x="total_orders",
                y="region",
                orientation="h",
                title="Orders by Region",
                labels={"total_orders": "Total Orders", "region": "Region"},
                color="total_revenue",
                color_continuous_scale="Blues"
            )
            fig.update_layout(height=450)
            st.plotly_chart(fig, use_container_width=True)

        # Revenue distribution
        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                regional,
                values="total_orders",
                names="region",
                title="Order Distribution by Region",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.pie(
                regional,
                values="total_revenue",
                names="region",
                title="Revenue Distribution by Region",
                hole=0.4
            )
            st.plotly_chart(fig, use_container_width=True)

        # Scatter plot
        fig = px.scatter(
            regional,
            x="total_orders",
            y="missing_rate",
            size="total_revenue",
            color="pct_orders_with_missing",
            text="region",
            title="Regional Performance: Orders vs Missing Rate",
            labels={
                "total_orders": "Total Orders",
                "missing_rate": "Missing Rate (%)",
                "pct_orders_with_missing": "% Orders with Issues"
            },
            color_continuous_scale="Reds"
        )
        fig.update_traces(textposition="top center")
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### Regional Comparison")

        comparison_df, stats = compare_regions(orders, metric="missing_rate")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Average Missing Rate", f"{stats['average']:.2f}%")

        with col2:
            st.metric("Best Region", stats["best_region"])

        with col3:
            st.metric("Worst Region", stats["worst_region"])

        # Comparison bar chart
        fig = px.bar(
            comparison_df.sort_values("vs_avg"),
            x="region",
            y="vs_avg",
            title="Missing Rate vs Average",
            labels={"vs_avg": "Difference from Average (%)", "region": "Region"},
            color="vs_avg",
            color_continuous_scale="RdYlGn_r"
        )
        fig.add_hline(y=0, line_dash="dash", line_color="black")
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        # Table
        st.markdown("#### Regional Statistics")
        display_cols = ["region", "total_orders", "missing_rate", "vs_avg", "is_above_avg", "is_outlier"]
        display_df = comparison_df[display_cols].copy()
        display_df["missing_rate"] = display_df["missing_rate"].round(2)
        display_df["vs_avg"] = display_df["vs_avg"].round(2)

        st.dataframe(
            display_df.sort_values("missing_rate", ascending=False),
            hide_index=True,
            use_container_width=True
        )

    with tab3:
        st.markdown("### Regional Hotspots")
        st.markdown("Regions with elevated fraud risk indicators.")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("#### High Missing Rate")
            if hotspots["high_missing_rate"]:
                for region in hotspots["high_missing_rate"]:
                    st.markdown(f"- 🔴 {region}")
            else:
                st.info("No hotspots detected")

        with col2:
            st.markdown("#### High Volume Missing")
            if hotspots["high_volume_missing"]:
                for region in hotspots["high_volume_missing"]:
                    st.markdown(f"- 🟠 {region}")
            else:
                st.info("No hotspots detected")

        with col3:
            st.markdown("#### Low Driver Coverage")
            if hotspots["low_driver_coverage"]:
                for region in hotspots["low_driver_coverage"]:
                    st.markdown(f"- 🟡 {region}")
            else:
                st.info("No hotspots detected")

        st.markdown("---")

        # Detailed table
        st.markdown("#### Detailed Regional Metrics")

        st.dataframe(
            regional.sort_values("missing_rate", ascending=False),
            hide_index=True,
            use_container_width=True
        )

        csv = regional.to_csv(index=False)
        st.download_button(
            label="Download Regional Report",
            data=csv,
            file_name="regional_analysis.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"Error: {str(e)}")

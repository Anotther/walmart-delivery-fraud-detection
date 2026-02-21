"""
Methodology Page - Data quality, structure, and analysis details.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import COLORS, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

st.set_page_config(
    page_title="Methodology - Walmart Fraud Detection",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

SEVERITY_COLORS = {
    "Critical": COLORS["critical"],
    "High": COLORS["warning"],
    "Medium": COLORS["walmart_blue_light"],
    "Low": COLORS["success"],
}
REQUIRED_METHOD_META_KEYS = {
    "generated_at",
    "total_orders",
    "total_drivers",
    "total_customers",
    "total_products",
    "date_start",
    "date_end",
    "quality_score",
    "total_issues",
    "quality_issue_breakdown",
    "schema_catalog",
    "pipeline_steps",
    "feature_catalog",
    "data_quality",
    "features",
}
METHODOLOGY_KPI_TOOLTIPS = {
    "deliveries_analyzed": (
        "Total order records included in methodology diagnostics for the selected analysis window."
    ),
    "entities_covered": (
        "Combined count of drivers, customers, and products represented in the methodology dataset."
    ),
    "data_quality_score": (
        "Composite data-quality score derived from completeness and validity checks across core tables."
    ),
    "order_level_issues": (
        "Orders flagged with structural issues such as missing IDs, negative values, or future dates."
    ),
    "features_engineered": (
        "Number of engineered fraud features currently active; delta shows the full catalog size "
        "tracked in metadata."
    ),
}


@st.cache_data(ttl=3000)
def get_methodology_metadata() -> Dict:
    """
    Fetch methodology metadata using lazy loading.
    This method uses a 30-minute TTL as methodology is reference material.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for methodology page
    page_data = cache.get_page_data('methodology')

    # Extract required metadata from page data
    meta = page_data['methodology_metadata']

    if isinstance(meta, dict) and REQUIRED_METHOD_META_KEYS.issubset(set(meta.keys())):
        return meta

    # Self-heal stale/legacy payloads from old cache layout.
    cache.clear_cache("methodology_metadata")
    cache.clear_cache("methodology_metadata_v2")
    cache.clear_page_cache('methodology')
    page_data = cache.get_page_data('methodology')
    return page_data['methodology_metadata']


def _quality_color(score: float) -> str:
    if score >= 98:
        return COLORS["success"]
    if score >= 95:
        return COLORS["warning"]
    return COLORS["critical"]


def _quality_label(score: float) -> str:
    if score >= 98:
        return "Stable quality baseline"
    if score >= 95:
        return "Moderate quality risk"
    return "High quality risk"


def _build_issue_frame(rows: List[Dict]) -> pd.DataFrame:
    issue_df = pd.DataFrame(rows)
    if issue_df.empty:
        return issue_df

    issue_df["count"] = pd.to_numeric(issue_df.get("count", 0), errors="coerce").fillna(0).astype(int)
    issue_df["rate_pct"] = pd.to_numeric(issue_df.get("rate_pct", 0.0), errors="coerce").fillna(0.0)
    issue_df["severity"] = issue_df.get("severity", "Low").astype(str)
    issue_df["scope"] = issue_df.get("scope", "N/A").astype(str)
    issue_df["issue"] = issue_df.get("issue", "Unknown").astype(str)
    issue_df["rate_label"] = issue_df["rate_pct"].map(lambda value: f"{value:.2f}%")
    issue_df = issue_df.sort_values(["count", "rate_pct"], ascending=[False, False]).reset_index(drop=True)
    return issue_df


def _render_header() -> None:
    st.markdown("### Operational Intelligence")
    st.markdown(
        """
        <div class="dashboard-header-row">
            <div>
                <h1 style="margin:0; font-size: 2.5rem;">Data Methodology & Quality</h1>
                <p class="text-muted">Quality diagnostics, schema lineage, and feature engineering transparency for the fraud analytics stack.</p>
            </div>
            <div class="scope-badge-container">
                 <span class="badge badge-success">Quality Governance</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")


def _render_schema_tab(schema_key: str, entry: Dict) -> None:
    if not entry:
        st.warning(f"No schema metadata available for {schema_key}.")
        return

    st.markdown(f"**Source**: {entry.get('source', 'N/A')}")
    st.markdown(f"**Primary Key**: `{entry.get('primary_key', 'N/A')}`")
    st.markdown(f"**Grain**: {entry.get('grain', 'N/A')}")
    key_links = entry.get("key_links", [])
    if key_links:
        key_links_label = ", ".join([f"`{item}`" for item in key_links])
        st.markdown(f"**Key Links**: {key_links_label}")
    st.caption(
        f"Rows: {int(entry.get('row_count', 0)):,} | Columns: {int(entry.get('column_count', 0)):,}"
    )

    columns_df = pd.DataFrame(entry.get("columns", []))
    if columns_df.empty:
        st.info("No column diagnostics available.")
        return

    for numeric_column in ["null_count", "null_pct"]:
        if numeric_column in columns_df.columns:
            columns_df[numeric_column] = pd.to_numeric(
                columns_df[numeric_column], errors="coerce"
            ).fillna(0)
    if "null_count" in columns_df.columns:
        columns_df["null_count"] = columns_df["null_count"].astype(int)
    if "null_pct" in columns_df.columns:
        columns_df["null_pct"] = columns_df["null_pct"].map(lambda value: f"{value:.2f}%")

    display_columns = ["column", "dtype", "null_count", "null_pct"]
    available_columns = [col for col in display_columns if col in columns_df.columns]
    st.dataframe(
        columns_df[available_columns].rename(
            columns={
                "column": "Column",
                "dtype": "Dtype",
                "null_count": "Null Count",
                "null_pct": "Null Rate",
            }
        ),
        use_container_width=True,
    )


def main() -> None:
    render_sidebar()
    _render_header()

    try:
        with st.spinner("Loading methodology lineage..."):
            meta = get_methodology_metadata()
    except Exception as exc:
        st.error(f"Error loading methodology metadata: {exc}")
        return

    if not isinstance(meta, dict) or not meta:
        st.warning("Methodology metadata is currently unavailable. Please refresh data and try again.")
        return

    total_orders = int(meta.get("total_orders", 0))
    total_drivers = int(meta.get("total_drivers", 0))
    total_customers = int(meta.get("total_customers", 0))
    total_products = int(meta.get("total_products", 0))
    quality_score = float(meta.get("quality_score", 0.0))
    total_issues = int(meta.get("total_issues", 0))
    features = meta.get("features", [])
    date_start = str(meta.get("date_start", "N/A"))
    date_end = str(meta.get("date_end", "N/A"))
    generated_at = str(meta.get("generated_at", "N/A"))

    st.caption(f"Last Updated: {generated_at} | Owner: Fraud Ops Team")

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card(
            "Deliveries Analyzed",
            f"{total_orders:,}",
            delta=f"{date_start} to {date_end}",
            delta_color="neutral",
            color=COLORS["walmart_blue"],
            tooltip=METHODOLOGY_KPI_TOOLTIPS["deliveries_analyzed"],
        )
    with k2:
        kpi_card(
            "Entities Covered",
            f"{total_drivers + total_customers + total_products:,}",
            delta=f"Drivers {total_drivers:,} | Customers {total_customers:,}",
            delta_color="neutral",
            color=COLORS["walmart_blue_light"],
            tooltip=METHODOLOGY_KPI_TOOLTIPS["entities_covered"],
        )
    with k3:
        kpi_card(
            "Data Quality Score",
            f"{quality_score:.2f}%",
            delta=_quality_label(quality_score),
            delta_color="neutral",
            color=_quality_color(quality_score),
            tooltip=METHODOLOGY_KPI_TOOLTIPS["data_quality_score"],
        )
    with k4:
        kpi_card(
            "Order-Level Issues",
            f"{total_issues:,}",
            delta="Missing IDs, negatives, and future dates",
            delta_color="neutral",
            color=COLORS["warning"] if total_issues > 0 else COLORS["success"],
            tooltip=METHODOLOGY_KPI_TOOLTIPS["order_level_issues"],
        )
    with k5:
        kpi_card(
            "Features Engineered",
            f"{len(features):,}",
            delta=f"Catalog size: {len(meta.get('feature_catalog', [])):,}",
            delta_color="neutral",
            color=COLORS["walmart_yellow"],
            tooltip=METHODOLOGY_KPI_TOOLTIPS["features_engineered"],
        )

    if total_orders == 0:
        st.warning("No order records are available for Methodology diagnostics. Showing static metadata only.")

    st.markdown("---")
    st.markdown("### Data Quality Diagnostics")

    issue_df = _build_issue_frame(meta.get("quality_issue_breakdown", []))
    if issue_df.empty:
        st.info("No quality issue diagnostics available.")
    else:
        chart_col, table_col = st.columns([2, 3])

        with chart_col:
            fig = px.bar(
                issue_df,
                x="issue",
                y="count",
                color="severity",
                color_discrete_map=SEVERITY_COLORS,
                text="rate_label",
            )
            fig.update_layout(
                xaxis_title="Issue Type",
                yaxis_title="Count",
                legend_title_text="Severity",
                margin=dict(t=20, l=10, r=10, b=70),
                plot_bgcolor=COLORS['plot_bg'],
                paper_bgcolor=COLORS['paper_bg'],
                font_family=COLORS['font_family'],
            )
            fig.update_xaxes(tickangle=-25)
            fig.update_traces(
                textposition="outside",
                customdata=issue_df[["rate_label", "scope"]].to_numpy(),
                hovertemplate=(
                    "Issue: %{x}<br>"
                    "Count: %{y}<br>"
                    "Rate: %{customdata[0]}<br>"
                    "Scope: %{customdata[1]}"
                    "<extra></extra>"
                ),
            )
            st.plotly_chart(fig, use_container_width=True)

        with table_col:
            st.markdown("#### Issue Breakdown Table")
            st.dataframe(
                issue_df[["issue", "scope", "count", "rate_label", "severity"]].rename(
                    columns={
                        "issue": "Issue",
                        "scope": "Scope",
                        "count": "Count",
                        "rate_label": "Rate (%)",
                        "severity": "Severity",
                    }
                ),
                use_container_width=True,
            )
            top_issue = issue_df.iloc[0]
            st.info(
                f"Primary exposure: {top_issue['issue']} ({top_issue['count']:,} records, {top_issue['rate_label']})."
            )

    st.markdown("---")
    st.markdown("### Schema & Lineage")

    schema_catalog = meta.get("schema_catalog", {})
    schema_tabs = st.tabs(["Orders", "Drivers", "Customers", "Products"])
    for tab_name, tab_key, tab in [
        ("Orders", "orders", schema_tabs[0]),
        ("Drivers", "drivers", schema_tabs[1]),
        ("Customers", "customers", schema_tabs[2]),
        ("Products", "products", schema_tabs[3]),
    ]:
        with tab:
            _render_schema_tab(tab_name, schema_catalog.get(tab_key, {}))

    st.markdown("---")
    st.markdown("### Pipeline Transformations")
    pipeline_df = pd.DataFrame(meta.get("pipeline_steps", []))
    if pipeline_df.empty:
        st.info("No pipeline transformation metadata available.")
    else:
        st.dataframe(
            pipeline_df.rename(
                columns={
                    "step": "Step",
                    "description": "Description",
                    "validation": "Validation",
                }
            ),
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### Feature Engineering Catalog")
    feature_df = pd.DataFrame(meta.get("feature_catalog", []))
    if feature_df.empty:
        st.info("No feature catalog metadata available.")
    else:
        st.dataframe(
            feature_df.rename(
                columns={
                    "feature": "Feature",
                    "formula": "Formula",
                    "owner": "Owner",
                    "purpose": "Purpose",
                }
            ),
            use_container_width=True,
        )

    st.markdown("---")
    with st.expander("View Raw Methodology Payload"):
        st.json(meta)


if __name__ == "__main__":
    main()

"""
Geographic Page - Regional geospatial risk intelligence.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config.viz_theme import PROJECT_THEME, REGION_COLORS
from src.dashboard.components import COLORS, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

st.set_page_config(
    page_title="Geographic - Walmart Fraud Detection",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

ITEM_VALUE_USD = 15.0
DEFAULT_COORD = (28.5383, -81.3792)  # Orlando center fallback
MAP_CENTER = {"lat": 28.57, "lon": -81.44}
REQUIRED_COLUMNS = [
    "region",
    "total_orders",
    "total_revenue",
    "items_missing",
    "orders_with_missing",
    "missing_rate",
    "pct_orders_with_missing",
    "revenue_share",
    "risk_rank",
]
REGION_COORDS: Dict[str, Tuple[float, float]] = {
    "Altamonte Springs": (28.6611, -81.3656),
    "Apopka": (28.6934, -81.5322),
    "Clermont": (28.5494, -81.7729),
    "Kissimmee": (28.2919, -81.4076),
    "Orlando": (28.5383, -81.3792),
    "Sanford": (28.8029, -81.2695),
    "Winter Park": (28.6003, -81.3392),
}
RISK_ORDER = ["Critical", "High", "Medium", "Low"]
RISK_COLORS = {
    "Critical": PROJECT_THEME["risk_colors"]["Critical"],
    "High": PROJECT_THEME["risk_colors"]["High"],
    "Medium": PROJECT_THEME["risk_colors"]["Medium"],
    "Low": PROJECT_THEME["risk_colors"]["Low"],
}
RISK_LABELS = {
    "Critical": "Critical [C]",
    "High": "High [H]",
    "Medium": "Medium [M]",
    "Low": "Low [L]",
}


@st.cache_data(ttl=600)  # 10-minute TTL for geographic data
def get_geo_data() -> pd.DataFrame:
    """
    Fetch geographic data using lazy loading.
    This method uses a 10-minute TTL as regional analysis updates periodically.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for geographic page
    page_data = cache.get_page_data('geographic')

    # Extract regional data from page data
    regional = page_data['regional_summary']

    return regional


def _query_param_value(name: str) -> str:
    value = st.query_params.get(name)
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


@st.cache_data(ttl=600)
def get_scoped_geo_data(product_id: str, product_category: str) -> pd.DataFrame:
    """
    Build regional metrics scoped to Product Analysis drill-down context.
    Returns empty DataFrame when no scoped events are available.
    """
    if not product_id and not product_category:
        return pd.DataFrame()

    cache = get_default_cache()
    workspace = cache.get_product_analysis_workspace()
    facts = workspace.get("missing_facts", pd.DataFrame()).copy()

    if facts.empty:
        return pd.DataFrame()

    if product_category:
        facts = facts[facts["category"].astype(str) == str(product_category)]
    if product_id:
        facts = facts[facts["product_id"].astype(str) == str(product_id)]

    if facts.empty:
        return pd.DataFrame()

    order_scope = (
        facts[
            [
                "order_id",
                "region",
                "order_amount",
                "items_delivered",
                "driver_id",
                "customer_id",
            ]
        ]
        .drop_duplicates(subset=["order_id"])
        .copy()
    )

    regional_orders = (
        order_scope.groupby("region", as_index=False)
        .agg(
            total_orders=("order_id", "nunique"),
            total_revenue=("order_amount", "sum"),
            items_delivered=("items_delivered", "sum"),
            unique_drivers=("driver_id", "nunique"),
            unique_customers=("customer_id", "nunique"),
        )
    )

    regional_missing = (
        facts.groupby("region", as_index=False)
        .agg(
            items_missing=("missing_item_id", "count"),
            orders_with_missing=("order_id", "nunique"),
        )
    )

    regional = regional_orders.merge(regional_missing, on="region", how="left")
    regional["items_missing"] = pd.to_numeric(regional["items_missing"], errors="coerce").fillna(0.0)
    regional["orders_with_missing"] = pd.to_numeric(
        regional["orders_with_missing"], errors="coerce"
    ).fillna(0.0)
    regional["items_delivered"] = pd.to_numeric(regional["items_delivered"], errors="coerce").fillna(0.0)

    regional["total_items"] = regional["items_delivered"] + regional["items_missing"]
    regional["missing_rate"] = np.where(
        regional["total_items"] > 0,
        (regional["items_missing"] / regional["total_items"]) * 100,
        0.0,
    )
    regional["pct_orders_with_missing"] = np.where(
        regional["total_orders"] > 0,
        (regional["orders_with_missing"] / regional["total_orders"]) * 100,
        0.0,
    )
    regional["orders_per_driver"] = np.where(
        regional["unique_drivers"] > 0,
        regional["total_orders"] / regional["unique_drivers"],
        0.0,
    )
    regional["orders_per_customer"] = np.where(
        regional["unique_customers"] > 0,
        regional["total_orders"] / regional["unique_customers"],
        0.0,
    )
    total_revenue = float(regional["total_revenue"].sum())
    regional["revenue_share"] = np.where(
        total_revenue > 0,
        (regional["total_revenue"] / total_revenue) * 100,
        0.0,
    )
    regional["risk_rank"] = regional["missing_rate"].rank(ascending=False, method="dense").astype(int)

    cols = [
        "region",
        "total_orders",
        "total_revenue",
        "items_missing",
        "orders_with_missing",
        "missing_rate",
        "pct_orders_with_missing",
        "revenue_share",
        "risk_rank",
    ]
    return regional[cols].sort_values("missing_rate", ascending=False)


def load_geographic_page_css() -> None:
    st.markdown(
        """
        <style>
          .geo-section-subtitle {
            color: #475569;
            font-size: 0.86rem;
            margin-top: -0.2rem;
            margin-bottom: 0.55rem;
          }
          .geo-table-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
          }
          .geo-table-head {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            align-items: center;
            padding: 0.78rem 0.9rem;
            border-bottom: 1px solid var(--border-light);
            background: #fafbfc;
          }
          .geo-table-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--walmart-blue-dark);
          }
          .geo-table-note {
            color: #64748b;
            font-size: 0.8rem;
          }
          .geo-legend {
            display: flex;
            gap: 0.35rem;
            flex-wrap: wrap;
            padding: 0.65rem 0.88rem 0;
          }
          .geo-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.12rem 0.48rem;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
          }
          .geo-chip-critical {
            background: #fee2e2;
            border-color: #fca5a5;
            color: #991b1b;
          }
          .geo-chip-high {
            background: #ffedd5;
            border-color: #fdba74;
            color: #9a3412;
          }
          .geo-chip-medium {
            background: #fef3c7;
            border-color: #fcd34d;
            color: #92400e;
          }
          .geo-chip-low {
            background: #dcfce7;
            border-color: #86efac;
            color: #166534;
          }
          .geo-table-wrap {
            width: 100%;
            overflow-x: auto;
            padding: 0.55rem 0.88rem 0.88rem;
          }
          .geo-table {
            width: 100%;
            border-collapse: collapse;
            min-width: 1040px;
          }
          .geo-table thead th {
            background: #f8fafc;
            text-align: left;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            color: #64748b;
            font-weight: 700;
            padding: 0.56rem 0.58rem;
            border-bottom: 1px solid var(--border-light);
          }
          .geo-table tbody td {
            font-size: 0.84rem;
            color: #0f172a;
            padding: 0.52rem 0.58rem;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
            white-space: nowrap;
            line-height: 1.25;
          }
          .geo-table tbody tr:last-child td {
            border-bottom: none;
          }
          .geo-table tbody tr:nth-child(even) {
            background: #fcfdff;
          }
          .geo-table tbody tr:hover {
            background: #f0f9ff;
          }
          .geo-table th.num,
          .geo-table td.num {
            text-align: right;
          }
          .geo-table th.center,
          .geo-table td.center {
            text-align: center;
          }
          .geo-region-cell {
            font-weight: 700;
            color: #0f172a;
          }
          .geo-gap-pos {
            color: #991b1b;
            font-weight: 700;
          }
          .geo-gap-neg {
            color: #166534;
            font-weight: 700;
          }
          .geo-gap-neu {
            color: #475569;
            font-weight: 600;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def validate_columns(df: pd.DataFrame) -> List[str]:
    return [col for col in REQUIRED_COLUMNS if col not in df.columns]


def classify_risk_tier(rank: int) -> str:
    if rank <= 1:
        return "Critical"
    if rank <= 2:
        return "High"
    if rank <= 4:
        return "Medium"
    return "Low"


def format_signed(value: float) -> str:
    return f"+{value:.2f}" if value > 0 else f"{value:.2f}"


def prepare_geographic_dataset(regional_df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str], float]:
    geo_df = regional_df.copy()
    geo_df["risk_rank"] = (
        pd.to_numeric(geo_df["risk_rank"], errors="coerce")
        .fillna(len(geo_df) + 1)
        .round()
        .astype(int)
    )
    geo_df["risk_tier"] = geo_df["risk_rank"].apply(classify_risk_tier)
    geo_df["estimated_loss_usd"] = geo_df["items_missing"] * ITEM_VALUE_USD
    avg_missing_rate = float(geo_df["missing_rate"].mean()) if not geo_df.empty else 0.0
    geo_df["missing_rate_gap"] = geo_df["missing_rate"] - avg_missing_rate

    geo_df["lat"] = geo_df["region"].map(lambda region: REGION_COORDS.get(region, (None, None))[0])
    geo_df["lon"] = geo_df["region"].map(lambda region: REGION_COORDS.get(region, (None, None))[1])

    fallback_regions = geo_df[geo_df["lat"].isna() | geo_df["lon"].isna()]["region"].astype(str).tolist()
    geo_df["lat"] = geo_df["lat"].fillna(DEFAULT_COORD[0])
    geo_df["lon"] = geo_df["lon"].fillna(DEFAULT_COORD[1])

    color_fallback = COLORS["walmart_blue_light"]
    geo_df["region_color"] = geo_df["region"].map(
        lambda region: REGION_COLORS.get(str(region), color_fallback)
    )
    return geo_df.sort_values("missing_rate", ascending=False), fallback_regions, avg_missing_rate


def get_region_color_map(regions: List[str]) -> Dict[str, str]:
    return {
        region: REGION_COLORS.get(region, COLORS["walmart_blue_light"])
        for region in regions
    }


def build_bubble_map(geo_df: pd.DataFrame) -> go.Figure:
    fig = px.scatter_map(
        geo_df,
        lat="lat",
        lon="lon",
        size="total_orders",
        color="region",
        size_max=34,
        zoom=8,
        center=MAP_CENTER,
        map_style="carto-positron",
        color_discrete_map=get_region_color_map(geo_df["region"].astype(str).tolist()),
        hover_name="region",
        hover_data={
            "lat": False,
            "lon": False,
            "missing_rate": ":.2f",
            "pct_orders_with_missing": ":.2f",
            "total_orders": ":,",
            "items_missing": ":,",
            "estimated_loss_usd": ":,.0f",
            "revenue_share": ":.2f",
        },
        labels={
            "missing_rate": "Missing Rate (%)",
            "pct_orders_with_missing": "Orders with Missing (%)",
            "total_orders": "Total Orders",
            "items_missing": "Missing Items",
            "estimated_loss_usd": "Est. Loss ($)",
            "revenue_share": "Revenue Share (%)",
        },
    )
    fig.update_traces(marker=dict(opacity=0.85))
    fig.update_layout(
        template="walmart_fraud",
        font_family=COLORS['font_family'],
        margin=dict(t=12, r=12, b=8, l=8),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="left",
            x=0,
            title_text="",
        ),
    )
    return fig


def build_missing_rate_chart(geo_df: pd.DataFrame, avg_missing_rate: float) -> go.Figure:
    chart_df = geo_df.sort_values("missing_rate", ascending=True)
    fig = px.bar(
        chart_df,
        x="missing_rate",
        y="region",
        orientation="h",
        text="missing_rate",
        color="region",
        color_discrete_map=get_region_color_map(chart_df["region"].astype(str).tolist()),
        labels={"missing_rate": "Missing Rate (%)", "region": "Region"},
    )
    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Missing Rate: %{x:.2f}%<extra></extra>",
    )
    fig.add_vline(
        x=avg_missing_rate,
        line_dash="dash",
        line_color=COLORS["warning"],
        annotation_text=f"Average {avg_missing_rate:.2f}%",
        annotation_position="top right",
    )
    fig.update_layout(
        template="walmart_fraud",
        font_family=COLORS['font_family'],
        margin=dict(t=12, r=16, b=8, l=8),
        yaxis_title=None,
        xaxis_title="Missing Rate (%)",
        showlegend=False,
    )
    return fig


def build_risk_volume_scatter(geo_df: pd.DataFrame, avg_missing_rate: float) -> go.Figure:
    avg_orders = float(geo_df["total_orders"].mean()) if not geo_df.empty else 0.0
    fig = px.scatter(
        geo_df,
        x="total_orders",
        y="missing_rate",
        color="risk_tier",
        size="items_missing",
        color_discrete_map=RISK_COLORS,
        category_orders={"risk_tier": RISK_ORDER},
        hover_name="region",
        hover_data={
            "risk_tier": True,
            "total_orders": ":,",
            "items_missing": ":,",
            "missing_rate": ":.2f",
            "missing_rate_gap": ":.2f",
        },
        labels={
            "total_orders": "Total Orders",
            "missing_rate": "Missing Rate (%)",
            "items_missing": "Missing Items",
            "missing_rate_gap": "Gap vs Avg (pp)",
            "risk_tier": "Risk Tier",
        },
    )
    fig.add_hline(
        y=avg_missing_rate,
        line_dash="dot",
        line_color=COLORS["warning"],
        annotation_text=f"Avg Missing Rate {avg_missing_rate:.2f}%",
        annotation_position="top left",
    )
    fig.add_vline(
        x=avg_orders,
        line_dash="dot",
        line_color=COLORS["walmart_blue"],
        annotation_text=f"Avg Orders {avg_orders:.0f}",
        annotation_position="top right",
    )
    fig.update_layout(
        template="walmart_fraud",
        font_family=COLORS['font_family'],
        margin=dict(t=12, r=12, b=8, l=8),
        legend_title_text="Risk Tier",
    )
    return fig


def build_revenue_share_chart(geo_df: pd.DataFrame) -> go.Figure:
    chart_df = geo_df.sort_values("revenue_share", ascending=True)
    fig = px.bar(
        chart_df,
        x="revenue_share",
        y="region",
        orientation="h",
        text="revenue_share",
        color="region",
        color_discrete_map=get_region_color_map(chart_df["region"].astype(str).tolist()),
        labels={"revenue_share": "Revenue Share (%)", "region": "Region"},
    )
    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Revenue Share: %{x:.2f}%<extra></extra>",
    )
    fig.update_layout(
        template="walmart_fraud",
        font_family=COLORS['font_family'],
        margin=dict(t=12, r=16, b=8, l=8),
        yaxis_title=None,
        xaxis_title="Revenue Share (%)",
        showlegend=False,
    )
    return fig


def build_risk_chip(tier: str) -> str:
    tier_class = tier.lower()
    safe_label = escape(RISK_LABELS.get(tier, tier))
    return f"<span class='geo-chip geo-chip-{tier_class}'>{safe_label}</span>"


def get_sort_config(sort_mode: str) -> Tuple[str, bool]:
    sort_config = {
        "Risk Rank": ("risk_rank", True),
        "Missing Rate (Highest)": ("missing_rate", False),
        "Gap vs Avg (Highest)": ("missing_rate_gap", False),
        "Orders with Missing (Highest)": ("pct_orders_with_missing", False),
        "Orders Volume (Highest)": ("total_orders", False),
        "Revenue Share (Highest)": ("revenue_share", False),
        "Estimated Loss (Highest)": ("estimated_loss_usd", False),
    }
    return sort_config.get(sort_mode, ("risk_rank", True))


def filter_and_sort_table(
    geo_df: pd.DataFrame,
    search_term: str,
    selected_risks: List[str],
    sort_mode: str,
) -> pd.DataFrame:
    view_df = geo_df.copy()
    if search_term:
        view_df = view_df[view_df["region"].str.contains(search_term, case=False, na=False)]
    if selected_risks:
        view_df = view_df[view_df["risk_tier"].isin(selected_risks)]

    sort_col, ascending = get_sort_config(sort_mode)
    return view_df.sort_values(sort_col, ascending=ascending)


def build_raw_numeric_table(view_df: pd.DataFrame) -> pd.DataFrame:
    return view_df[
        [
            "region",
            "risk_rank",
            "risk_tier",
            "total_orders",
            "missing_rate",
            "missing_rate_gap",
            "pct_orders_with_missing",
            "revenue_share",
            "items_missing",
            "estimated_loss_usd",
        ]
    ].rename(
        columns={
            "region": "Region",
            "risk_rank": "Rank",
            "risk_tier": "Risk",
            "total_orders": "Volume",
            "missing_rate": "Rate (%)",
            "missing_rate_gap": "Gap vs Avg (pp)",
            "pct_orders_with_missing": "Orders with Missing (%)",
            "revenue_share": "Revenue Share (%)",
            "items_missing": "Missing Items",
            "estimated_loss_usd": "Est. Loss ($)",
        }
    )


def render_regional_table(table_df: pd.DataFrame, avg_missing_rate: float) -> None:
    if table_df.empty:
        st.warning("No regions match the current table filters.")
        return

    rows = []

    for _, row in table_df.iterrows():
        risk_tier = str(row.get("risk_tier", "Low"))
        gap = float(row.get("missing_rate_gap", 0.0))
        if gap > 0.01:
            gap_class = "geo-gap-pos"
        elif gap < -0.01:
            gap_class = "geo-gap-neg"
        else:
            gap_class = "geo-gap-neu"

        rows.append(
            (
                "<tr>"
                f"<td class='center'>{int(row.get('risk_rank', 0))}</td>"
                f"<td class='geo-region-cell'>{escape(str(row.get('region', '-')))}</td>"
                f"<td class='center'>{build_risk_chip(risk_tier)}</td>"
                f"<td class='center'>{float(row.get('missing_rate', 0.0)):.2f}%</td>"
                f"<td class='center'><span class='{gap_class}'>{format_signed(gap)} pp</span></td>"
                f"<td class='num'>{int(row.get('total_orders', 0)):,}</td>"
                f"<td class='center'>{float(row.get('pct_orders_with_missing', 0.0)):.2f}%</td>"
                f"<td class='num'>{float(row.get('revenue_share', 0.0)):.2f}%</td>"
                f"<td class='num'>${float(row.get('estimated_loss_usd', 0.0)):,.0f}</td>"
                "</tr>"
            )
        )

    table_html = f"""
    <div class="geo-table-card">
      <div class="geo-table-head">
        <div class="geo-table-title">Regional Command Table</div>
        <div class="geo-table-note">
          {len(table_df)} regions shown, avg benchmark {avg_missing_rate:.2f}%.
        </div>
      </div>
      <div class="geo-table-wrap">
        <table class="geo-table">
          <thead>
            <tr>
              <th class="center">Rank</th>
              <th>Region</th>
              <th class="center">Risk</th>
              <th class="center">Missing Rate</th>
              <th class="center">Gap vs Avg</th>
              <th class="num">Orders</th>
              <th class="center">Orders w/ Missing</th>
              <th class="num">Revenue Share</th>
              <th class="num">Est. Loss</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def render_raw_regional_table(raw_numeric: pd.DataFrame) -> None:
    if raw_numeric.empty:
        st.info("No raw rows available for the current filters.")
        return

    rows = []
    for _, row in raw_numeric.iterrows():
        risk_tier = str(row.get("Risk", "Low"))
        gap_value = float(row.get("Gap vs Avg (pp)", 0.0))
        gap_class = "geo-gap-pos" if gap_value > 0.01 else "geo-gap-neg" if gap_value < -0.01 else "geo-gap-neu"

        rows.append(
            (
                "<tr>"
                f"<td>{escape(str(row.get('Region', '-')))}</td>"
                f"<td class='center'>{int(row.get('Rank', 0))}</td>"
                f"<td class='center'>{build_risk_chip(risk_tier)}</td>"
                f"<td class='num'>{int(row.get('Volume', 0)):,}</td>"
                f"<td class='center'>{float(row.get('Rate (%)', 0.0)):.2f}%</td>"
                f"<td class='center'><span class='{gap_class}'>{float(row.get('Gap vs Avg (pp)', 0.0)):+.2f} pp</span></td>"
                f"<td class='center'>{float(row.get('Orders with Missing (%)', 0.0)):.2f}%</td>"
                f"<td class='num'>{float(row.get('Revenue Share (%)', 0.0)):.2f}%</td>"
                f"<td class='num'>{int(row.get('Missing Items', 0)):,}</td>"
                f"<td class='num'>${float(row.get('Est. Loss ($)', 0.0)):,.0f}</td>"
                "</tr>"
            )
        )

    table_html = f"""
    <div class="geo-table-card">
      <div class="geo-table-head">
        <div class="geo-table-title">Raw Regional Dataset</div>
        <div class="geo-table-note">
          Same visual pattern as the command table with full numeric detail.
        </div>
      </div>
      <div class="geo-table-wrap">
        <table class="geo-table">
          <thead>
            <tr>
              <th>Region</th>
              <th class="center">Rank</th>
              <th class="center">Risk</th>
              <th class="num">Volume</th>
              <th class="center">Rate (%)</th>
              <th class="center">Gap vs Avg</th>
              <th class="center">Orders w/ Missing</th>
              <th class="num">Revenue Share</th>
              <th class="num">Missing Items</th>
              <th class="num">Est. Loss</th>
            </tr>
          </thead>
          <tbody>
            {''.join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def main() -> None:
    render_sidebar()
    load_geographic_page_css()

    st.markdown("### Operational Intelligence")
    st.markdown(
        """
        <div class="dashboard-header-row">
            <div>
                <h1 style="margin:0; font-size: 2.5rem;">Geographic Intelligence Hub</h1>
                <p class="text-muted">Regional hotspots, geospatial exposure, and execution priorities for Central Florida.</p>
            </div>
            <div class="scope-badge-container">
                 <span class="badge badge-success">Regional Scope</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")

    scope_product = _query_param_value("product_id")
    scope_category = _query_param_value("product_category")
    scope_source = _query_param_value("source_page")

    with st.spinner("Loading regional data..."):
        if scope_product or scope_category:
            regional_df = get_scoped_geo_data(scope_product, scope_category)
            if regional_df.empty:
                st.warning(
                    "No regional records for incoming Product Analysis scope. "
                    "Falling back to full regional dataset."
                )
                regional_df = get_geo_data()
            else:
                st.info(
                    "Scoped geographic view active: "
                    f"product_id={scope_product or 'All'} | "
                    f"category={scope_category or 'All'} "
                    f"(source: {scope_source or 'product_analysis'})"
                )
        else:
            regional_df = get_geo_data()

    if regional_df.empty:
        st.info("No regional data available.")
        return

    missing_columns = validate_columns(regional_df)
    if missing_columns:
        st.error(f"Regional dataset is missing required columns: {', '.join(missing_columns)}")
        return

    geo_df, fallback_regions, avg_missing_rate = prepare_geographic_dataset(regional_df)
    if fallback_regions:
        st.caption(
            "Coordinate fallback used for: " + ", ".join(sorted(set(fallback_regions)))
        )

    worst_region = geo_df.iloc[0]
    best_region = geo_df.iloc[-1]
    total_regions = len(geo_df)
    total_loss = float(geo_df["estimated_loss_usd"].sum())
    spread = float(worst_region["missing_rate"] - best_region["missing_rate"])

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Regions Monitored", f"{total_regions}", delta="Central Florida Coverage", color=COLORS["walmart_blue"])
    with k2:
        kpi_card(
            "Average Missing Rate",
            f"{avg_missing_rate:.2f}%",
            delta=f"Spread {spread:.2f} pp",
            color=COLORS["warning"],
        )
    with k3:
        kpi_card(
            "Highest Risk Region",
            str(worst_region["region"]),
            delta=f"{float(worst_region['missing_rate']):.2f}%",
            delta_color="inverse",
            color=COLORS["critical"],
        )
    with k4:
        kpi_card(
            "Lowest Risk Region",
            str(best_region["region"]),
            delta=f"{float(best_region['missing_rate']):.2f}%",
            color=COLORS["success"],
        )
    with k5:
        kpi_card(
            "Estimated Regional Loss",
            f"${total_loss:,.0f}",
            delta="$15 per missing item",
            color=COLORS["critical"],
        )

    st.markdown("---")

    map_col, rank_col = st.columns([1.55, 1.0])
    with map_col:
        st.markdown("#### Central Florida Bubble Map")
        st.markdown(
            "<div class='geo-section-subtitle'>Bubble size = order volume, hover includes risk and loss context.</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_bubble_map(geo_df), use_container_width=True)

    with rank_col:
        st.markdown("#### Missing Rate Ranking")
        st.markdown(
            "<div class='geo-section-subtitle'>Regions ordered by missing rate with average baseline.</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_missing_rate_chart(geo_df, avg_missing_rate), use_container_width=True)

    scatter_col, revenue_col = st.columns([1.35, 1.0])
    with scatter_col:
        st.markdown("#### Risk vs Volume Matrix")
        st.markdown(
            "<div class='geo-section-subtitle'>Reference lines show average missing rate and average order volume.</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_risk_volume_scatter(geo_df, avg_missing_rate), use_container_width=True)

    with revenue_col:
        st.markdown("#### Revenue Share by Region")
        st.markdown(
            "<div class='geo-section-subtitle'>Regional revenue contribution supports route and audit prioritization.</div>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(build_revenue_share_chart(geo_df), use_container_width=True)

    st.markdown("---")
    filter_col1, filter_col2, filter_col3 = st.columns([2.2, 1.8, 1.9])
    with filter_col1:
        table_search = st.text_input(
            "Find region in table",
            placeholder="Type a region name...",
            key="geo_table_search",
        )
    with filter_col2:
        table_risks = st.multiselect(
            "Risk filter",
            options=RISK_ORDER,
            default=RISK_ORDER,
            key="geo_table_risks",
        )
    with filter_col3:
        table_sort_mode = st.selectbox(
            "Sort table by",
            options=[
                "Risk Rank",
                "Missing Rate (Highest)",
                "Gap vs Avg (Highest)",
                "Orders with Missing (Highest)",
                "Orders Volume (Highest)",
                "Revenue Share (Highest)",
                "Estimated Loss (Highest)",
            ],
            index=0,
            key="geo_table_sort_mode",
        )

    table_view = filter_and_sort_table(
        geo_df=geo_df,
        search_term=table_search,
        selected_risks=table_risks,
        sort_mode=table_sort_mode,
    )
    render_regional_table(table_view, avg_missing_rate)

    with st.expander("Raw Regional Dataset"):
        raw_numeric = build_raw_numeric_table(table_view)
        render_raw_regional_table(raw_numeric)
        st.download_button(
            "Download raw regional CSV",
            data=raw_numeric.to_csv(index=False).encode("utf-8"),
            file_name="regional_dataset_filtered.csv",
            mime="text/csv",
            use_container_width=True,
        )

if __name__ == "__main__":
    main()

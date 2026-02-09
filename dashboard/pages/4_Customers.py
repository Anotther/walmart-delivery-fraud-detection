"""
Customers Page - Customer-specific fraud investigation workbench.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import COLORS, insight_card, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

RISK_ORDER = ["Low", "Medium", "High", "Critical"]
SEGMENT_ORDER = ["Low Value", "Medium Value", "High Value", "Premium"]
RISK_COLORS = {
    "Low": COLORS["success"],
    "Medium": COLORS["walmart_yellow"],
    "High": COLORS["warning"],
    "Critical": COLORS["critical"],
}
SIGNATURE_META = {
    "Always Claiming": ("Immediate validation", COLORS["critical"]),
    "High-Value Opportunist": ("Value abuse pattern", COLORS["warning"]),
    "Chronic Reporter": ("Repeat behavior", COLORS["warning"]),
    "Emerging Risk": ("Monitor closely", COLORS["walmart_blue"]),
    "Baseline Pattern": ("Normal behavior", COLORS["success"]),
}
SLA_BY_RISK = {
    "Critical": "4h",
    "High": "12h",
    "Medium": "48h",
    "Low": "72h",
}

st.set_page_config(
    page_title="Customers - Walmart Fraud Detection",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()


def load_customers_page_css() -> None:
    """Inject page-level CSS focused on light-mode contrast and queue consistency."""
    st.markdown(
        """
        <style>
          :root {
            --cx-surface: #FFFFFF;
            --cx-surface-soft: #F8FAFC;
            --cx-text-strong: #0F172A;
            --cx-text-body: #1E293B;
            --cx-text-muted: #475569;
            --cx-border: #CBD5E1;
            --cx-border-soft: #E2E8F0;
            --cx-focus: #1D4ED8;
            --cx-shadow: 0 1px 2px rgba(15, 23, 42, 0.06), 0 8px 20px rgba(15, 23, 42, 0.06);
          }

          .text-muted {
            color: var(--cx-text-muted) !important;
          }

          .kpi-card {
            border-color: var(--cx-border) !important;
            box-shadow: var(--cx-shadow);
          }

          [data-testid="stDataFrame"] {
            border-color: var(--cx-border) !important;
            box-shadow: var(--cx-shadow);
          }

          [data-testid="stMetricLabel"] p {
            color: var(--cx-text-body) !important;
            font-weight: 600 !important;
          }

          [data-testid="stMetricDelta"] {
            color: var(--cx-text-body) !important;
          }

          button[role="tab"] {
            color: var(--cx-text-body) !important;
          }

          button[role="tab"][aria-selected="true"] {
            color: #003695 !important;
          }

          div[data-baseweb="select"] > div {
            border-color: var(--cx-border) !important;
          }

          div[data-baseweb="select"] > div:focus-within {
            border-color: var(--cx-focus) !important;
            box-shadow: 0 0 0 1px var(--cx-focus) !important;
          }

          .customer-queue-card {
            border: 1px solid var(--cx-border) !important;
            box-shadow: var(--cx-shadow);
          }

          .customer-queue-card .consistency-header {
            background: var(--cx-surface-soft) !important;
            border-bottom: 1px solid var(--cx-border) !important;
          }

          .customer-queue-title {
            font-size: 0.98rem;
            font-weight: 700;
            color: var(--cx-text-strong);
            margin: 0;
          }

          .customer-queue-subtitle {
            margin-top: 0.2rem;
            font-size: 0.82rem;
            color: var(--cx-text-muted);
          }

          .customer-queue-table {
            width: 100%;
            border-collapse: collapse;
          }

          .customer-queue-table thead th {
            text-align: left;
            font-size: 0.73rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            color: #334155;
            font-weight: 700;
            padding: 0.55rem 0.65rem;
            background: #f8fafc;
            border-bottom: 1px solid var(--cx-border);
            white-space: nowrap;
          }

          .customer-queue-table tbody td {
            font-size: 0.85rem;
            color: var(--cx-text-body);
            padding: 0.56rem 0.65rem;
            border-bottom: 1px solid var(--cx-border-soft);
            vertical-align: middle;
            white-space: nowrap;
          }

          .customer-queue-table tbody tr:last-child td {
            border-bottom: none;
          }

          .customer-queue-table tbody tr:nth-child(even) {
            background: #fcfdff;
          }

          .customer-queue-table tbody tr:hover {
            background: #eff6ff;
          }

          .customer-queue-table th.num,
          .customer-queue-table td.num {
            text-align: right;
          }

          .customer-risk-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.12rem 0.5rem;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid transparent;
          }

          .customer-risk-pill.risk-low {
            background: #dcfce7;
            border-color: #86efac;
            color: #166534;
          }

          .customer-risk-pill.risk-medium {
            background: #fef3c7;
            border-color: #fcd34d;
            color: #92400e;
          }

          .customer-risk-pill.risk-high {
            background: #ffedd5;
            border-color: #fdba74;
            color: #9a3412;
          }

          .customer-risk-pill.risk-critical {
            background: #fee2e2;
            border-color: #fca5a5;
            color: #991b1b;
          }

          .customer-priority-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.12rem 0.48rem;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid #cbd5e1;
            color: #334155;
            background: #f8fafc;
          }

          .customer-priority-chip.priority-immediate {
            color: #991b1b;
            border-color: #fca5a5;
            background: #fee2e2;
          }

          .customer-priority-chip.priority-fast-track {
            color: #9a3412;
            border-color: #fdba74;
            background: #ffedd5;
          }

          .customer-priority-chip.priority-review {
            color: #92400e;
            border-color: #fcd34d;
            background: #fef3c7;
          }

          .customer-priority-chip.priority-monitor {
            color: #334155;
            border-color: #cbd5e1;
            background: #f8fafc;
          }

          .customer-case-header {
            background: var(--cx-surface);
            border: 1px solid var(--cx-border);
            border-radius: 12px;
            padding: 0.8rem 1rem;
            box-shadow: var(--cx-shadow);
            margin-bottom: 0.9rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _normalize_0_1(series: pd.Series) -> pd.Series:
    clean = pd.to_numeric(series, errors="coerce").fillna(0.0)
    span = float(clean.max() - clean.min())
    if span == 0:
        return pd.Series(np.zeros(len(clean), dtype=float), index=clean.index)
    return (clean - clean.min()) / span


def _percent(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce").fillna(0.0)
    den = pd.to_numeric(denominator, errors="coerce").fillna(0.0)
    return pd.Series(np.where(den > 0, (num / den) * 100, 0.0), index=num.index)


def _assign_behavior_signature(customer_df: pd.DataFrame) -> pd.DataFrame:
    df = customer_df.copy()

    high_claim_rate = max(8.0, float(df["claim_rate"].quantile(0.85)))
    high_claim_orders = max(35.0, float(df["pct_orders_with_claims"].quantile(0.80)))
    high_value = max(120.0, float(df["avg_order_value"].quantile(0.75)))
    repeat_claim_threshold = max(2, int(df["orders_with_claims"].quantile(0.80)))

    conditions = [
        (df["pct_orders_with_claims"] >= 80) & (df["total_orders"] >= 3),
        (df["claim_rate"] >= high_claim_rate)
        & (df["pct_orders_with_claims"] >= high_claim_orders)
        & (df["avg_order_value"] >= high_value)
        & (df["orders_with_claims"] >= 2),
        (df["orders_with_claims"] >= repeat_claim_threshold) & (df["total_orders"] >= 4),
        (df["risk_score"] >= 60) & (df["total_orders"] < 4),
    ]
    values = [
        "Always Claiming",
        "High-Value Opportunist",
        "Chronic Reporter",
        "Emerging Risk",
    ]

    df["behavior_signature"] = np.select(conditions, values, default="Baseline Pattern")
    signature_rank = {name: idx for idx, name in enumerate(SIGNATURE_META.keys(), start=1)}
    df["signature_rank"] = df["behavior_signature"].map(signature_rank).fillna(99).astype(int)
    return df


def _compute_case_priority(customer_df: pd.DataFrame) -> pd.DataFrame:
    df = customer_df.copy()
    spend_norm = _normalize_0_1(df["total_spent"])
    claims_norm = _normalize_0_1(df["orders_with_claims"])

    df["priority_score"] = (
        df["risk_score"] * 0.50
        + df["pct_orders_with_claims"] * 0.20
        + (spend_norm * 100) * 0.15
        + (claims_norm * 100) * 0.15
    ).clip(0, 100)

    df["priority_tier"] = pd.cut(
        df["priority_score"],
        bins=[-1, 35, 60, 80, 100],
        labels=["Monitor", "Review", "Fast Track", "Immediate"],
    ).astype(str)
    return df


@st.cache_data(ttl=600)
def get_customer_workspace() -> Dict[str, pd.DataFrame]:
    cache = get_default_cache()

    customers = cache.get_customer_summary().copy()
    orders = cache._load_orders_with_features().copy()
    drivers = cache.get_driver_summary().copy()

    customer_numeric = [
        "total_orders",
        "total_spent",
        "items_received",
        "items_reported_missing",
        "orders_with_claims",
        "claim_rate",
        "pct_orders_with_claims",
        "avg_order_value",
        "risk_score",
    ]
    for col in customer_numeric:
        if col in customers.columns:
            customers[col] = pd.to_numeric(customers[col], errors="coerce").fillna(0.0)

    customers["risk_category"] = customers["risk_category"].astype(str).replace("nan", "Low")
    customers["spending_segment"] = customers["spending_segment"].astype(str).replace("nan", "Low Value")

    orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
    orders = orders.dropna(subset=["order_date"]).copy()
    for col in ["items_delivered", "items_missing", "order_amount", "total_items"]:
        if col in orders.columns:
            orders[col] = pd.to_numeric(orders[col], errors="coerce").fillna(0.0)

    orders["total_items"] = np.where(
        orders["total_items"] > 0,
        orders["total_items"],
        orders["items_delivered"] + orders["items_missing"],
    )
    orders["has_claim"] = orders["items_missing"] > 0
    orders["month_period"] = orders["order_date"].dt.to_period("M").astype(str)

    customer_activity = (
        orders.groupby("customer_id")
        .agg(
            first_order_date=("order_date", "min"),
            last_order_date=("order_date", "max"),
            active_days=("order_date", lambda s: int((s.max() - s.min()).days) + 1),
            unique_drivers=("driver_id", "nunique"),
            unique_regions=("region", "nunique"),
        )
        .reset_index()
    )
    customers = customers.merge(customer_activity, on="customer_id", how="left")
    customers["active_days"] = pd.to_numeric(customers["active_days"], errors="coerce").fillna(0).astype(int)
    customers["unique_drivers"] = pd.to_numeric(customers["unique_drivers"], errors="coerce").fillna(0).astype(int)
    customers["unique_regions"] = pd.to_numeric(customers["unique_regions"], errors="coerce").fillna(0).astype(int)

    customers = _assign_behavior_signature(customers)
    customers = _compute_case_priority(customers)

    driver_cols = ["driver_id", "driver_name", "risk_category", "risk_score", "missing_rate"]
    drivers = drivers[driver_cols].copy()
    drivers = drivers.rename(
        columns={
            "risk_category": "driver_risk_category",
            "risk_score": "driver_risk_score",
            "missing_rate": "driver_missing_rate",
        }
    )
    drivers["driver_risk_category"] = drivers["driver_risk_category"].astype(str).replace("nan", "Low")
    drivers["driver_risk_score"] = pd.to_numeric(drivers["driver_risk_score"], errors="coerce").fillna(0.0)
    drivers["driver_missing_rate"] = pd.to_numeric(drivers["driver_missing_rate"], errors="coerce").fillna(0.0)

    return {"customers": customers, "orders": orders, "drivers": drivers}


def apply_filters(
    customer_df: pd.DataFrame,
    search_term: str,
    selected_risks: list[str],
    selected_segment: str,
    min_priority: int,
    min_orders: int,
    repeat_only: bool,
) -> pd.DataFrame:
    df = customer_df.copy()

    if selected_risks:
        df = df[df["risk_category"].isin(selected_risks)]

    if selected_segment != "All":
        df = df[df["spending_segment"] == selected_segment]

    df = df[df["priority_score"] >= float(min_priority)]
    df = df[df["total_orders"] >= float(min_orders)]

    if repeat_only:
        df = df[df["orders_with_claims"] >= 2]

    query = search_term.strip()
    if query:
        name_mask = df["customer_name"].astype(str).str.contains(query, case=False, na=False)
        id_mask = df["customer_id"].astype(str).str.contains(query, case=False, na=False)
        df = df[name_mask | id_mask]

    return df


def build_case_queue(customer_df: pd.DataFrame) -> pd.DataFrame:
    return customer_df.sort_values(
        by=["priority_score", "risk_score", "orders_with_claims", "claim_rate"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def build_segment_matrix(customer_df: pd.DataFrame) -> pd.DataFrame:
    matrix = customer_df.pivot_table(
        index="spending_segment",
        columns="risk_category",
        values="customer_id",
        aggfunc="count",
        fill_value=0,
    )
    row_order = [seg for seg in SEGMENT_ORDER if seg in matrix.index]
    col_order = [risk for risk in RISK_ORDER if risk in matrix.columns]
    return matrix.reindex(index=row_order, columns=col_order, fill_value=0)


def build_customer_monthly(customer_orders: pd.DataFrame) -> pd.DataFrame:
    if customer_orders.empty:
        return pd.DataFrame()

    monthly = (
        customer_orders.groupby("month_period")
        .agg(
            orders=("order_id", "count"),
            claim_orders=("has_claim", "sum"),
            items_missing=("items_missing", "sum"),
            total_items=("total_items", "sum"),
            revenue=("order_amount", "sum"),
        )
        .reset_index()
    )
    monthly["claim_rate"] = _percent(monthly["items_missing"], monthly["total_items"])
    monthly["claim_order_rate"] = _percent(monthly["claim_orders"], monthly["orders"])
    monthly["month_date"] = pd.to_datetime(monthly["month_period"], errors="coerce")
    return monthly.sort_values("month_date")


def build_driver_links(
    customer_orders: pd.DataFrame,
    driver_df: pd.DataFrame,
    selected_risk_score: float,
) -> pd.DataFrame:
    if customer_orders.empty:
        return pd.DataFrame()

    links = (
        customer_orders.groupby("driver_id")
        .agg(
            interactions=("order_id", "count"),
            items_missing=("items_missing", "sum"),
            total_items=("total_items", "sum"),
            last_order=("order_date", "max"),
        )
        .reset_index()
    )
    links["pair_missing_rate"] = _percent(links["items_missing"], links["total_items"])

    links = links.merge(driver_df, on="driver_id", how="left")
    links["driver_name"] = links["driver_name"].fillna(links["driver_id"].astype(str))
    links["driver_risk_category"] = links["driver_risk_category"].fillna("Low")
    links["driver_risk_score"] = pd.to_numeric(links["driver_risk_score"], errors="coerce").fillna(0.0)
    links["risk_gap"] = (links["driver_risk_score"] - float(selected_risk_score)).round(2)

    high_link = (
        (links["interactions"] >= 3)
        & (links["pair_missing_rate"] >= 20.0)
        & (links["driver_risk_category"].isin(["High", "Critical"]))
    )
    watch_link = (
        (links["interactions"] >= 2)
        & (links["pair_missing_rate"] >= 10.0)
    )

    links["link_status"] = np.select(
        [high_link, watch_link],
        ["High Link Risk", "Watch Link"],
        default="Low Link Risk",
    )

    links["sla_hours"] = np.select(
        [links["link_status"] == "High Link Risk", links["link_status"] == "Watch Link"],
        ["24h", "48h"],
        default="72h",
    )
    links["period_label"] = links["last_order"].dt.strftime("%Y-%m")
    return links.sort_values(["interactions", "pair_missing_rate"], ascending=[False, False])


def render_queue_table(queue_df: pd.DataFrame) -> None:
    if queue_df.empty:
        st.info("No customer cases match the selected scope.")
        return

    rows = []
    for _, row in queue_df.head(12).iterrows():
        risk = str(row["risk_category"])
        risk_css = f"risk-{risk.lower().replace(' ', '-')}"
        period = "-"
        if pd.notna(row.get("last_order_date")):
            period = pd.to_datetime(row["last_order_date"]).strftime("%Y-%m-%d")
        priority_tier = str(row.get("priority_tier", "Monitor"))
        priority_css = f"priority-{priority_tier.lower().replace(' ', '-')}"

        rows.append(
            "<tr>"
            f"<td>{escape(str(row['customer_id']))}</td>"
            f"<td>{escape(str(row['customer_name']))}</td>"
            f"<td><span class='customer-risk-pill {risk_css}'>{escape(risk)}</span></td>"
            f"<td class='num'><span class='customer-priority-chip {priority_css}'>"
            f"{escape(priority_tier)} · {float(row['priority_score']):.1f}</span></td>"
            f"<td class='num'>{float(row['claim_rate']):.1f}%</td>"
            f"<td class='num'>{int(row['orders_with_claims'])}</td>"
            f"<td class='num'>{escape(period)}</td>"
            f"<td class='num'>{escape(SLA_BY_RISK.get(risk, '72h'))}</td>"
            "</tr>"
        )

    table_html = f"""
    <div class="consistency-wrap customer-queue-card">
      <div class="consistency-header">
        <div>
          <p class="customer-queue-title">Customer Investigation Queue</p>
          <div class="customer-queue-subtitle">
            Priority + SLA + risk labels support triage without relying on color alone.
          </div>
        </div>
      </div>
      <div style="overflow-x:auto;">
        <table class="customer-queue-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Risk</th>
              <th class="num">Priority</th>
              <th class="num">Claim Rate</th>
              <th class="num">Claim Orders</th>
              <th class="num">Last Order</th>
              <th class="num">SLA</th>
            </tr>
          </thead>
          <tbody>
            {"".join(rows)}
          </tbody>
        </table>
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)


def case_action_text(customer_row: pd.Series, links_df: pd.DataFrame) -> Tuple[str, str]:
    priority = str(customer_row["priority_tier"])
    signature = str(customer_row["behavior_signature"])

    if priority == "Immediate":
        primary = "Manual claim validation + proof-of-delivery required."
    elif priority == "Fast Track":
        primary = "Apply selective friction: one-time PIN on high-value orders."
    elif priority == "Review":
        primary = "Monitor next 3 orders and trigger alert if another claim appears."
    else:
        primary = "Standard monitoring only."

    if not links_df.empty and (links_df["link_status"] == "High Link Risk").any():
        secondary = "Audit repeated customer-driver pairs with high missing rates."
    elif signature == "High-Value Opportunist":
        secondary = "Prioritize basket-level review on premium products."
    elif signature == "Chronic Reporter":
        secondary = "Run behavioral interview workflow before refunds."
    else:
        secondary = "No collusion signal; keep baseline control policy."

    return primary, secondary


def main() -> None:
    render_sidebar()
    load_customers_page_css()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Customer Scope")
        min_priority = st.slider("Min case priority", min_value=0, max_value=100, value=55, step=5)
        min_orders = st.slider("Min orders", min_value=1, max_value=20, value=2, step=1)
        repeat_only = st.checkbox("Only repeat claimers", value=True)
        st.caption("Applies to queue and all detail modules in this page.")

    header_col, refresh_col = st.columns([6, 1])
    with header_col:
        st.markdown("### Customer Intelligence")
        st.markdown(
            """
            <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:0.75rem;">
              <div>
                <h1 style="margin:0; font-size:2.25rem;">Customer Case Workbench</h1>
                <p class="text-muted" style="margin-top:0.25rem;">
                  Dedicated triage flow for repeat claims, behavior signatures, and customer-driver links.
                </p>
              </div>
              <div>
                <span class="badge badge-success">Customer Focus</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with refresh_col:
        st.markdown("<div style='height:1.65rem;'></div>", unsafe_allow_html=True)
        if st.button("Refresh", use_container_width=True):
            cache = get_default_cache()
            cache.refresh_all()
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    workspace = get_customer_workspace()
    customers = workspace["customers"]
    orders = workspace["orders"]
    drivers = workspace["drivers"]

    if customers.empty:
        st.info("No customer data available.")
        return

    filter_col1, filter_col2, filter_col3 = st.columns([2.3, 1.6, 1.2])
    with filter_col1:
        search_term = st.text_input(
            "Search customer",
            placeholder="Name or customer ID",
        )
    with filter_col2:
        selected_risks = st.multiselect(
            "Risk category",
            options=[risk for risk in RISK_ORDER if risk in customers["risk_category"].unique()],
            default=[risk for risk in ["Critical", "High"] if risk in customers["risk_category"].unique()],
        )
    with filter_col3:
        segments = [seg for seg in SEGMENT_ORDER if seg in customers["spending_segment"].unique()]
        selected_segment = st.selectbox("Spending segment", options=["All"] + segments, index=0)

    filtered = apply_filters(
        customer_df=customers,
        search_term=search_term,
        selected_risks=selected_risks,
        selected_segment=selected_segment,
        min_priority=min_priority,
        min_orders=min_orders,
        repeat_only=repeat_only,
    )

    total_filtered = len(filtered)
    critical_count = int((filtered["risk_category"] == "Critical").sum())
    repeat_count = int((filtered["orders_with_claims"] >= 3).sum())
    avg_claim = float(filtered["claim_rate"].mean()) if total_filtered else 0.0
    exposure_usd = float(filtered["items_reported_missing"].sum() * 15.0) if total_filtered else 0.0
    queue_share = (total_filtered / len(customers) * 100) if len(customers) else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card("Case Queue", f"{total_filtered}", delta=f"{queue_share:.1f}% of customers", color=COLORS["walmart_blue"])
    with k2:
        kpi_card("Critical Cases", f"{critical_count}", delta="SLA: 4h", delta_color="inverse", color=COLORS["critical"])
    with k3:
        kpi_card("Repeat Offenders", f"{repeat_count}", delta="3+ claim orders", delta_color="inverse", color=COLORS["warning"])
    with k4:
        kpi_card("Avg Claim Rate", f"{avg_claim:.2f}%", delta="Items missing / items ordered", color=COLORS["walmart_blue_light"])
    with k5:
        kpi_card("Estimated Exposure", f"${exposure_usd:,.0f}", delta="$15 per missing item", color=COLORS["critical"])

    st.markdown("---")

    matrix_col, scatter_col = st.columns([1.15, 1.85])
    with matrix_col:
        st.markdown("#### Segment x Risk Matrix")
        matrix = build_segment_matrix(filtered if not filtered.empty else customers)
        if matrix.empty:
            st.info("No matrix data for selected filters.")
        else:
            fig_matrix = px.imshow(
                matrix.values,
                x=matrix.columns.tolist(),
                y=matrix.index.tolist(),
                text_auto=True,
                labels={"x": "Risk Category", "y": "Spending Segment", "color": "Customers"},
                color_continuous_scale=["#F3F4F6", COLORS["walmart_blue_light"]],
            )
            fig_matrix.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_color="#1E293B",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis=dict(
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                ),
                yaxis=dict(
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                ),
                coloraxis_colorbar=dict(
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
            )
            st.plotly_chart(fig_matrix, width="stretch")

    with scatter_col:
        st.markdown("#### Risk Concentration by Spend")
        if filtered.empty:
            st.info("No customers in current scope.")
        else:
            risk_palette = {k: RISK_COLORS[k] for k in RISK_COLORS if k in filtered["risk_category"].unique()}
            fig_scatter = px.scatter(
                filtered,
                x="avg_order_value",
                y="claim_rate",
                size="total_orders",
                color="risk_category",
                color_discrete_map=risk_palette,
                hover_data={
                    "customer_name": True,
                    "risk_score": ":.1f",
                    "priority_score": ":.1f",
                    "orders_with_claims": True,
                    "avg_order_value": ":.2f",
                    "claim_rate": ":.2f",
                },
                labels={
                    "avg_order_value": "Average Order Value ($)",
                    "claim_rate": "Claim Rate (%)",
                    "risk_category": "Risk Category",
                },
            )
            portfolio_baseline = float(customers["claim_rate"].mean()) if len(customers) else 0.0
            value_threshold = float(customers["avg_order_value"].quantile(0.75))
            fig_scatter.add_hline(
                y=portfolio_baseline,
                line_dash="dash",
                line_color=COLORS["warning"],
                annotation_text=f"Portfolio baseline {portfolio_baseline:.2f}%",
            )
            fig_scatter.add_vline(
                x=value_threshold,
                line_dash="dot",
                line_color=COLORS["walmart_blue"],
                annotation_text="High-value threshold",
            )
            fig_scatter.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_color="#1E293B",
                legend_title_text="Risk Category",
                margin=dict(t=10, r=8, b=8, l=8),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
            )
            fig_scatter.update_traces(
                marker=dict(line=dict(width=0.6, color="#E2E8F0")),
                hovertemplate=(
                    "Customer: %{customdata[0]}<br>"
                    "Avg Value: $%{x:.2f}<br>"
                    "Claim Rate: %{y:.2f}%<br>"
                    "Risk Score: %{customdata[1]:.1f}<br>"
                    "Priority: %{customdata[2]:.1f}<extra></extra>"
                ),
            )
            st.plotly_chart(fig_scatter, width="stretch")

    st.markdown("---")

    queue = build_case_queue(filtered)

    st.markdown("#### Investigation Queue")
    st.caption("Review prioritized customers, then open a case to continue the investigation workbench.")
    render_queue_table(queue)

    if queue.empty:
        return

    customer_options = queue["customer_id"].astype(str).tolist()
    selected_customer_id = st.selectbox(
        "Open customer case",
        options=customer_options,
        format_func=lambda cid: (
            f"{queue.loc[queue['customer_id'].astype(str) == cid, 'customer_name'].iloc[0]} "
            f"({queue.loc[queue['customer_id'].astype(str) == cid, 'priority_score'].iloc[0]:.1f})"
        ),
    )

    exploratory_view = queue.copy()
    exploratory_view["SLA"] = exploratory_view["risk_category"].map(SLA_BY_RISK).fillna("72h")
    exploratory_view["Gap"] = (exploratory_view["priority_score"] - exploratory_view["risk_score"]).round(2)
    exploratory_view["Claim Rate"] = exploratory_view["claim_rate"].round(2)
    exploratory_view["Claim Orders"] = exploratory_view["orders_with_claims"].astype(int)
    exploratory_view["Period"] = pd.to_datetime(
        exploratory_view["last_order_date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")

    with st.expander("Exploratory queue table", expanded=False):
        st.dataframe(
            exploratory_view[
                [
                    "customer_id",
                    "customer_name",
                    "priority_tier",
                    "SLA",
                    "Gap",
                    "Claim Rate",
                    "Claim Orders",
                    "Period",
                ]
            ].rename(columns={"priority_tier": "Priority Tier"}),
            width="stretch",
            hide_index=True,
        )

    st.markdown("---")

    selected_row = queue[queue["customer_id"].astype(str) == selected_customer_id].iloc[0]
    selected_signature = str(selected_row["behavior_signature"])
    signature_label, signature_color = SIGNATURE_META.get(
        selected_signature,
        ("Monitor", COLORS["text_light"]),
    )

    st.markdown(
        f"""
        <div class="customer-case-header">
          <strong style="font-size:1rem; color:#0F172A;">Case Detail</strong>
          <div style="font-size:0.86rem; color:#475569; margin-top:0.2rem;">
            Active customer: {escape(str(selected_row['customer_name']))}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(f"#### Case Detail: {selected_row['customer_name']}")
    d1, d2, d3 = st.columns([1.1, 1.1, 1.1])
    with d1:
        case_risk = str(selected_row["risk_category"])
        risk_css = f"risk-{case_risk.lower().replace(' ', '-')}"
        st.markdown(
            f"<span class='customer-risk-pill {risk_css}'>{escape(case_risk)}</span>",
            unsafe_allow_html=True,
        )
        st.caption(f"Risk score: {selected_row['risk_score']:.1f}")
    with d2:
        st.markdown(
            (
                "<div style='display:inline-block; padding:0.25rem 0.55rem; border-radius:999px;"
                f"background:{signature_color}20; color:{signature_color}; font-size:0.8rem; font-weight:700;'>"
                f"{escape(selected_signature)}</div>"
            ),
            unsafe_allow_html=True,
        )
        st.caption(signature_label)
    with d3:
        st.metric("Priority score", f"{selected_row['priority_score']:.1f}", selected_row["priority_tier"])

    stat1, stat2, stat3, stat4 = st.columns(4)
    with stat1:
        st.metric("Total orders", int(selected_row["total_orders"]))
    with stat2:
        st.metric("Orders with claims", int(selected_row["orders_with_claims"]))
    with stat3:
        st.metric("Claim rate", f"{selected_row['claim_rate']:.2f}%")
    with stat4:
        st.metric("Total spent", f"${selected_row['total_spent']:,.0f}")

    selected_orders = orders[orders["customer_id"] == selected_row["customer_id"]].copy()
    monthly = build_customer_monthly(selected_orders)
    links = build_driver_links(selected_orders, drivers, float(selected_row["risk_score"]))

    tab_timeline, tab_links, tab_actions = st.tabs(
        ["Claim Timeline", "Driver Links", "Action Simulator"]
    )

    with tab_timeline:
        if monthly.empty:
            st.info("No timeline data for this customer.")
        else:
            fig_timeline = go.Figure()
            fig_timeline.add_trace(
                go.Bar(
                    x=monthly["month_period"],
                    y=monthly["claim_orders"],
                    name="Claim Orders",
                    marker_color=COLORS["walmart_blue_light"],
                )
            )
            fig_timeline.add_trace(
                go.Scatter(
                    x=monthly["month_period"],
                    y=monthly["claim_rate"],
                    name="Claim Rate (%)",
                    yaxis="y2",
                    mode="lines+markers",
                    line=dict(color=COLORS["critical"], width=2.5),
                    marker=dict(size=7),
                )
            )

            portfolio_baseline = float(customers["claim_rate"].mean()) if len(customers) else 0.0
            fig_timeline.add_hline(
                y=portfolio_baseline,
                line_dash="dash",
                line_color=COLORS["warning"],
                yref="y2",
                annotation_text=f"Portfolio baseline {portfolio_baseline:.2f}%",
            )

            fig_timeline.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_color="#1E293B",
                margin=dict(t=24, l=8, r=8, b=8),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
                yaxis=dict(
                    title="Claim Orders",
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
                yaxis2=dict(
                    title="Claim Rate (%)",
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
                hovermode="x unified",
            )
            st.plotly_chart(fig_timeline, width="stretch")

            last_window = monthly.tail(3)
            trend = "increasing" if last_window["claim_rate"].is_monotonic_increasing else "unstable"
            insight_card(
                "Behavior trend",
                (
                    f"Last {len(last_window)} periods show {trend} claim-rate behavior. "
                    f"Current peak: {monthly['claim_rate'].max():.2f}%."
                ),
                icon="Case",
                compact=True,
            )

    with tab_links:
        if links.empty:
            st.info("No customer-driver links available.")
        else:
            status_map = {
                "High Link Risk": COLORS["critical"],
                "Watch Link": COLORS["warning"],
                "Low Link Risk": COLORS["success"],
            }
            fig_links = px.bar(
                links.head(10).sort_values("interactions", ascending=True),
                x="interactions",
                y="driver_name",
                orientation="h",
                color="link_status",
                color_discrete_map=status_map,
                hover_data={
                    "pair_missing_rate": ":.2f",
                    "driver_risk_score": ":.2f",
                    "items_missing": True,
                },
                labels={"interactions": "Interactions", "driver_name": "Driver"},
            )
            fig_links.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                font_family="Inter",
                font_color="#1E293B",
                margin=dict(t=10, l=8, r=8, b=8),
                legend_title_text="Link Status",
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
                yaxis=dict(
                    showgrid=False,
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    titlefont=dict(color="#334155"),
                ),
            )
            fig_links.update_traces(
                hovertemplate=(
                    "Driver: %{y}<br>"
                    "Interactions: %{x}<br>"
                    "Pair Missing Rate: %{customdata[0]:.2f}%<br>"
                    "Driver Risk Score: %{customdata[1]:.2f}<extra></extra>"
                )
            )
            st.plotly_chart(fig_links, width="stretch")

            links_view = links.copy()
            links_view["Rate"] = links_view["pair_missing_rate"].round(2)
            links_view["Volume"] = links_view["interactions"].astype(int)
            links_view["SLA"] = links_view["sla_hours"]
            links_view["Gap"] = links_view["risk_gap"].round(2)
            links_view["Period"] = links_view["period_label"]

            st.dataframe(
                links_view[
                    [
                        "driver_name",
                        "link_status",
                        "driver_risk_category",
                        "SLA",
                        "Gap",
                        "Rate",
                        "Volume",
                        "Period",
                    ]
                ].rename(
                    columns={
                        "driver_name": "Driver",
                        "link_status": "Link Signal",
                        "driver_risk_category": "Driver Risk",
                    }
                ),
                width="stretch",
                hide_index=True,
            )

    with tab_actions:
        primary_action, secondary_action = case_action_text(selected_row, links)
        insight_card("Primary action", primary_action, icon="Plan", compact=True)
        insight_card("Secondary action", secondary_action, icon="Signal", compact=True)

        st.markdown("##### Impact simulator")
        coverage = st.slider(
            "Enhanced verification coverage (%)",
            min_value=10,
            max_value=100,
            value=60,
            step=5,
        )
        detection_lift = st.slider(
            "Expected claim detection uplift (%)",
            min_value=10,
            max_value=90,
            value=35,
            step=5,
        )

        prevented_items = (
            float(selected_row["items_reported_missing"])
            * (coverage / 100.0)
            * (detection_lift / 100.0)
        )
        prevented_loss = prevented_items * 15.0

        sim1, sim2, sim3 = st.columns(3)
        with sim1:
            st.metric("Covered claims", f"{coverage}%")
        with sim2:
            st.metric("Prevented items", f"{prevented_items:.1f}")
        with sim3:
            st.metric("Potential savings", f"${prevented_loss:,.0f}")


if __name__ == "__main__":
    main()

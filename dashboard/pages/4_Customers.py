"""
Customers Page - Customer-specific fraud investigation workbench.
"""
from __future__ import annotations

import sys
from html import escape
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.viz_theme import PROJECT_THEME
from src.dashboard.components import COLORS, insight_card, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

RISK_ORDER = ["Low", "Medium", "High", "Critical"]
SEGMENT_ORDER = ["Low Value", "Medium Value", "High Value", "Premium"]
RISK_COLORS = {
    "Low": PROJECT_THEME["risk_colors"]["Low"],
    "Medium": PROJECT_THEME["risk_colors"]["Medium"],
    "High": PROJECT_THEME["risk_colors"]["High"],
    "Critical": PROJECT_THEME["risk_colors"]["Critical"],
}
SIGNATURE_META = {
    "Always Claiming": ("Requires strict claim validation", COLORS["critical"]),
    "High-Value Opportunist": ("High-value abuse signal", COLORS["warning"]),
    "Chronic Reporter": ("Recurring claims behavior", COLORS["warning"]),
    "Emerging Risk": ("Watchlist signal", COLORS["walmart_blue"]),
    "Baseline Pattern": ("Normal behavior", COLORS["success"]),
}
SLA_BY_RISK = {
    "Critical": "4h",
    "High": "12h",
    "Medium": "48h",
    "Low": "72h",
}
CUSTOMERS_SELECTED_CASE_KEY = "customers_selected_case_id"
COPY = {
    "scope_title": "Customer Scope / Filters",
    "scope_context": "These filters impact KPIs, charts, investigation queue, and selected case details.",
    "queue_title": "Investigation Queue",
    "queue_context": "Applying Customer Scope filters.",
    "queue_subtitle": "Prioritize cases by Risk, Priority score, Claim Rate, and SLA. Click a row to open details.",
    "detail_context": "Details reflect the currently selected queue case.",
    "detail_empty": "No case selected. Adjust filters or click a case in the queue to inspect details.",
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
          .text-muted {
            color: var(--text-secondary) !important;
          }

          .customer-section-subtitle {
            color: var(--text-secondary);
            font-size: 0.86rem;
            margin-top: -0.2rem;
            margin-bottom: 0.55rem;
          }

          .kpi-card {
            border-color: var(--border-light) !important;
            box-shadow: var(--shadow-sm) !important;
          }

          [data-testid="stDataFrame"] {
            border-color: var(--border-light) !important;
            box-shadow: var(--shadow-sm) !important;
          }

          [data-testid="stMetricLabel"] p {
            color: var(--text-primary) !important;
            font-weight: 600 !important;
          }

          [data-testid="stMetricDelta"] {
            color: var(--text-primary) !important;
          }

          button[role="tab"] {
            color: var(--text-primary) !important;
          }

          button[role="tab"][aria-selected="true"] {
            color: var(--walmart-blue-dark) !important;
          }

          div[data-baseweb="select"] > div,
          div[data-baseweb="input"] > div {
            border-color: var(--border-light) !important;
          }

          div[data-baseweb="select"] > div:focus-within,
          div[data-baseweb="input"] > div:focus-within {
            border-color: var(--walmart-blue) !important;
            box-shadow: 0 0 0 1px var(--walmart-blue) !important;
          }

          .customer-queue-card {
            background: var(--bg-card);
            border: 1px solid var(--border-light) !important;
            box-shadow: var(--shadow-sm) !important;
          }

          .customer-queue-card .consistency-header {
            background: #fafbfc !important;
            border-bottom: 1px solid var(--border-light) !important;
            padding: 0.82rem 0.95rem !important;
          }

          .customer-queue-header-main {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 0.7rem;
            flex-wrap: wrap;
          }

          .customer-queue-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: var(--walmart-blue-dark);
            margin: 0;
          }

          .customer-queue-subtitle {
            margin-top: 0.2rem;
            font-size: 0.8rem;
            color: var(--text-secondary);
          }

          .customer-queue-legend {
            display: flex;
            gap: 0.3rem;
            flex-wrap: wrap;
            justify-content: flex-end;
            align-items: center;
          }

          .customer-legend-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.08rem 0.44rem;
            font-size: 0.7rem;
            font-weight: 700;
            border: 1px solid transparent;
            white-space: nowrap;
          }

          .customer-legend-chip.critical {
            background: #fee2e2;
            border-color: #fca5a5;
            color: #991b1b;
          }

          .customer-legend-chip.warning {
            background: #ffedd5;
            border-color: #fdba74;
            color: #9a3412;
          }

          .customer-legend-chip.stable {
            background: #dcfce7;
            border-color: #86efac;
            color: #166534;
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
            color: #64748b;
            font-weight: 700;
            padding: 0.5rem 0.58rem;
            background: #f8fafc;
            border-bottom: 1px solid var(--border-light);
            white-space: nowrap;
          }

          .customer-queue-table tbody td {
            font-size: 0.83rem;
            color: #0f172a;
            padding: 0.48rem 0.58rem;
            border-bottom: 1px solid #f1f5f9;
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
            padding: 0.1rem 0.46rem;
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
            background: var(--bg-card);
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 0.75rem 0.95rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 0.9rem;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _query_param_value(name: str) -> str:
    value = st.query_params.get(name)
    if value is None:
        return ""
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value)


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


@st.cache_data(ttl=900)  # 15-minute TTL for customer data
def get_customer_workspace() -> Dict[str, pd.DataFrame]:
    """
    Fetch customer workspace using lazy loading.
    This method uses a 15-minute TTL as customer behavior is stable.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for customer page
    page_data = cache.get_page_data('customers')

    # Extract customer data from page data
    customers = page_data['customer_summary'].copy()

    # Load additional data not in PAGE_CONFIGS
    orders = cache.get_orders_with_features().copy()
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


@st.cache_data(ttl=600)
def get_product_scope_customer_ids(product_id: str, product_category: str) -> set[str]:
    """Get impacted customers from Product Analysis drill-down params."""
    if not product_id and not product_category:
        return set()

    cache = get_default_cache()
    workspace = cache.get_product_analysis_workspace()
    missing_items = workspace.get("missing_items", pd.DataFrame()).copy()
    orders = workspace.get("orders", pd.DataFrame()).copy()

    if missing_items.empty or orders.empty:
        return set()

    if product_category:
        missing_items = missing_items[missing_items["category"].astype(str) == str(product_category)]
    if product_id:
        missing_items = missing_items[missing_items["product_id"].astype(str) == str(product_id)]

    if missing_items.empty:
        return set()

    order_ids = set(missing_items["order_id"].astype(str))
    scoped_orders = orders[orders["order_id"].astype(str).isin(order_ids)].copy()
    if scoped_orders.empty:
        return set()

    return set(scoped_orders["customer_id"].astype(str))


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


def resolve_selected_case_id(queue_df: pd.DataFrame) -> str:
    """Resolve the active case id using session state and queue contents."""
    if queue_df.empty:
        st.session_state.pop(CUSTOMERS_SELECTED_CASE_KEY, None)
        return ""

    available_ids = queue_df["customer_id"].astype(str).tolist()
    selected_case_id = str(st.session_state.get(CUSTOMERS_SELECTED_CASE_KEY, ""))
    if selected_case_id not in available_ids:
        selected_case_id = available_ids[0]
        st.session_state[CUSTOMERS_SELECTED_CASE_KEY] = selected_case_id
    return selected_case_id


def build_queue_display(queue_df: pd.DataFrame, selected_case_id: str, top_n: int = 12) -> pd.DataFrame:
    """Prepare queue dataframe for interactive grid rendering."""
    queue_view = queue_df.head(top_n).copy()
    queue_view["customer_id"] = queue_view["customer_id"].astype(str)
    queue_view["last_order_date"] = pd.to_datetime(queue_view["last_order_date"], errors="coerce")

    queue_view["Case"] = np.where(
        queue_view["customer_id"] == selected_case_id,
        "● Active",
        "",
    )
    queue_view["ID"] = queue_view["customer_id"]
    queue_view["Customer"] = queue_view["customer_name"].astype(str)
    queue_view["Risk"] = queue_view["risk_category"].astype(str)
    queue_view["Priority"] = (
        queue_view["priority_tier"].astype(str)
        + " · "
        + queue_view["priority_score"].map(lambda value: f"{float(value):.1f}")
    )
    queue_view["Claim Rate"] = queue_view["claim_rate"].map(lambda value: f"{float(value):.1f}%")
    queue_view["Claim Orders"] = pd.to_numeric(
        queue_view["orders_with_claims"], errors="coerce"
    ).fillna(0).astype(int)
    queue_view["Last Order"] = queue_view["last_order_date"].dt.strftime("%Y-%m-%d").fillna("-")
    queue_view["SLA"] = queue_view["risk_category"].map(SLA_BY_RISK).fillna("72h")

    return queue_view[
        [
            "Case",
            "ID",
            "Customer",
            "Risk",
            "Priority",
            "Claim Rate",
            "Claim Orders",
            "Last Order",
            "SLA",
        ]
    ]


def _selected_rows_from_event(event: Any) -> list[int]:
    if isinstance(event, dict):
        selection = event.get("selection", {})
        if isinstance(selection, dict):
            rows = selection.get("rows", [])
            if isinstance(rows, list):
                return [int(row) for row in rows]
    try:
        return [int(row) for row in event.selection.rows]  # type: ignore[attr-defined]
    except Exception:
        return []


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


def render_queue_table(queue_df: pd.DataFrame, selected_case_id: str) -> str:
    """Render interactive investigation queue and return active case id."""
    if queue_df.empty:
        st.info("No customer cases match the selected scope. Try reducing filter strictness.")
        return ""

    queue_view = build_queue_display(queue_df, selected_case_id=selected_case_id, top_n=12)
    queue_head = queue_df.head(12).copy().reset_index(drop=True)
    table_event = st.dataframe(
        queue_view,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="customers_investigation_queue_table",
        column_config={
            "Case": st.column_config.TextColumn("Case"),
            "ID": st.column_config.TextColumn("ID"),
            "Customer": st.column_config.TextColumn("Customer"),
            "Risk": st.column_config.TextColumn("Risk"),
            "Priority": st.column_config.TextColumn("Priority"),
            "Claim Rate": st.column_config.TextColumn("Claim Rate"),
            "Claim Orders": st.column_config.NumberColumn("Claim Orders", format="%d"),
            "Last Order": st.column_config.TextColumn("Last Order"),
            "SLA": st.column_config.TextColumn("SLA"),
        },
    )

    selected_rows = _selected_rows_from_event(table_event)
    if selected_rows:
        selected_row_idx = selected_rows[0]
        if 0 <= selected_row_idx < len(queue_head):
            selected_case_id = str(queue_head.iloc[selected_row_idx]["customer_id"])
            st.session_state[CUSTOMERS_SELECTED_CASE_KEY] = selected_case_id

    st.caption(f"Active case: {selected_case_id}")
    return selected_case_id


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

    header_col, refresh_col = st.columns([6, 1])
    with header_col:
        st.markdown("### Operational Intelligence")
        st.markdown(
            """
            <div class="dashboard-header-row">
              <div>
                <h1 style="margin:0; font-size:2.5rem;">Customer Intelligence Hub</h1>
                <p class="text-muted" style="margin-top:0.25rem;">
                  Customer-level triage for repeat claims, behavior signatures, and customer-driver links.
                </p>
              </div>
              <div class="scope-badge-container">
                <span class="badge badge-success">Customer Scope</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with refresh_col:
        st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Refresh Data", use_container_width=True):
            cache = get_default_cache()
            cache.refresh_all()
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    workspace = get_customer_workspace()
    customers = workspace["customers"]
    orders = workspace["orders"]
    drivers = workspace["drivers"]

    scope_product = _query_param_value("product_id")
    scope_category = _query_param_value("product_category")
    scope_source = _query_param_value("source_page")
    if scope_product or scope_category:
        scoped_customer_ids = get_product_scope_customer_ids(scope_product, scope_category)
        if scoped_customer_ids:
            customers = customers[customers["customer_id"].astype(str).isin(scoped_customer_ids)].copy()
            orders = orders[orders["customer_id"].astype(str).isin(scoped_customer_ids)].copy()
            st.info(
                "Scoped customer analysis active: "
                f"product_id={scope_product or 'All'} | "
                f"category={scope_category or 'All'} | "
                f"customers={len(customers)} "
                f"(source: {scope_source or 'product_analysis'})"
            )
        else:
            st.warning(
                "No impacted customers found for incoming Product Analysis scope. "
                "Showing empty scoped view."
            )

    if customers.empty:
        st.info("No customer data available.")
        return

    st.markdown(f"#### {COPY['scope_title']}")
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

    scope_ops_col1, scope_ops_col2, scope_ops_col3 = st.columns([1.4, 1.2, 1.2])
    with scope_ops_col1:
        min_priority = st.slider("Min priority score", min_value=0, max_value=100, value=55, step=5)
    with scope_ops_col2:
        min_orders = st.slider("Min total orders", min_value=1, max_value=20, value=2, step=1)
    with scope_ops_col3:
        repeat_only = st.checkbox("Only repeat claimers", value=True)

    customer_scope: Dict[str, Any] = {
        "search_term": search_term,
        "selected_risks": selected_risks,
        "selected_segment": selected_segment,
        "min_priority": min_priority,
        "min_orders": min_orders,
        "repeat_only": repeat_only,
    }

    st.markdown(
        f"<div class='customer-section-subtitle'>{COPY['scope_context']}</div>",
        unsafe_allow_html=True,
    )

    filtered = apply_filters(
        customer_df=customers,
        search_term=str(customer_scope["search_term"]),
        selected_risks=list(customer_scope["selected_risks"]),
        selected_segment=str(customer_scope["selected_segment"]),
        min_priority=int(customer_scope["min_priority"]),
        min_orders=int(customer_scope["min_orders"]),
        repeat_only=bool(customer_scope["repeat_only"]),
    )

    total_filtered = len(filtered)
    critical_count = int((filtered["risk_category"] == "Critical").sum())
    repeat_count = int((filtered["orders_with_claims"] >= 3).sum())
    avg_claim = float(filtered["claim_rate"].mean()) if total_filtered else 0.0
    exposure_usd = float(filtered["items_reported_missing"].sum() * 15.0) if total_filtered else 0.0
    queue_share = (total_filtered / len(customers) * 100) if len(customers) else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        kpi_card(
            "Case Queue",
            f"{total_filtered}",
            delta=f"{queue_share:.1f}% of customers",
            color=COLORS["walmart_blue"],
            tooltip=(
                "Calculation: count(customers) after all page filters and triage thresholds. "
                "Source: customer_summary + scoped orders from dashboard cache. "
                "Interpretation: operational investigation workload in current scope."
            ),
        )
    with k2:
        kpi_card(
            "Critical Cases",
            f"{critical_count}",
            delta="SLA: 4h",
            delta_color="inverse",
            color=COLORS["critical"],
            tooltip=(
                "Calculation: count(risk_category == 'Critical') in filtered queue. "
                "Source: customer risk categorization from customer_summary. "
                "Interpretation: highest-priority cases requiring immediate triage."
            ),
        )
    with k3:
        kpi_card(
            "Repeat Offenders",
            f"{repeat_count}",
            delta="3+ claim orders",
            delta_color="inverse",
            color=COLORS["warning"],
            tooltip=(
                "Calculation: count(orders_with_claims >= 3) in filtered customers. "
                "Source: customer_summary aggregated from orders and missing items. "
                "Interpretation: recurrent claim behavior requiring deeper validation."
            ),
        )
    with k4:
        kpi_card(
            "Avg Claim Rate",
            f"{avg_claim:.2f}%",
            delta="Items missing / items ordered",
            color=COLORS["walmart_blue_light"],
            tooltip=(
                "Calculation: mean(claim_rate) where claim_rate = items_reported_missing / "
                "(items_received + items_reported_missing) * 100. "
                "Source: customer_summary built from order-level facts. "
                "Interpretation: average severity of customer claims in scope."
            ),
        )
    with k5:
        kpi_card(
            "Estimated Exposure",
            f"${exposure_usd:,.0f}",
            delta="$15 per missing item",
            color=COLORS["critical"],
            tooltip=(
                "Calculation: sum(items_reported_missing) * $15 proxy. "
                "Source: filtered customer_summary claim volume. "
                "Interpretation: estimated financial exposure linked to current queue."
            ),
        )

    st.markdown("---")

    queue = build_case_queue(filtered)

    st.markdown(f"#### {COPY['queue_title']}")
    st.caption(COPY["queue_context"])
    st.markdown(
        f"<div class='customer-section-subtitle'>{COPY['queue_subtitle']}</div>",
        unsafe_allow_html=True,
    )

    selected_customer_id = resolve_selected_case_id(queue)
    selected_customer_id = render_queue_table(queue, selected_case_id=selected_customer_id)
    selected_row = None
    if selected_customer_id and not queue.empty:
        selected_match = queue[queue["customer_id"].astype(str) == selected_customer_id]
        if not selected_match.empty:
            selected_row = selected_match.iloc[0]

    exploratory_view = queue.copy()
    exploratory_view["SLA"] = exploratory_view["risk_category"].map(SLA_BY_RISK).fillna("72h")
    exploratory_view["Gap"] = (exploratory_view["priority_score"] - exploratory_view["risk_score"]).round(2)
    exploratory_view["Rate"] = exploratory_view["claim_rate"].round(2)
    exploratory_view["Volume"] = exploratory_view["orders_with_claims"].astype(int)
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
                    "Rate",
                    "Volume",
                    "Period",
                ]
            ].rename(columns={"priority_tier": "Priority Tier"}),
            use_container_width=True,
            hide_index=True,
        )

    st.markdown("---")

    st.markdown("#### Case Detail")
    st.caption(COPY["detail_context"])

    if selected_row is None:
        st.info(COPY["detail_empty"])
        selected_orders = pd.DataFrame()
        monthly = pd.DataFrame()
        links = pd.DataFrame()
    else:
        selected_signature = str(selected_row["behavior_signature"])
        signature_label, signature_color = SIGNATURE_META.get(
            selected_signature,
            ("Monitor signal", COLORS["text_light"]),
        )

        st.markdown(
            f"""
            <div class="customer-case-header">
              <strong style="font-size:1rem; color:#0F172A;">
                Case Detail - {escape(str(selected_row['customer_name']))}
              </strong>
              <div style="font-size:0.86rem; color:#475569; margin-top:0.2rem;">
                Active case from queue
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("##### Status & Risk")
        risk_col, risk_score_col, priority_col, priority_score_col, behavior_col = st.columns([1, 1, 1, 1, 1.4])
        with risk_col:
            st.metric("Risk tier", str(selected_row["risk_category"]))
        with risk_score_col:
            st.metric("Risk score", f"{selected_row['risk_score']:.1f}")
        with priority_col:
            st.metric("Priority tier", str(selected_row["priority_tier"]))
        with priority_score_col:
            st.metric(
                "Priority score",
                f"{selected_row['priority_score']:.1f}",
                help=(
                    "Calculation: weighted triage score derived from risk score, claim rate, "
                    "repetition behavior, and spend context for the selected customer."
                ),
            )
        with behavior_col:
            st.caption("Behavior signal")
            st.markdown(
                (
                    "<div style='display:inline-block; padding:0.25rem 0.55rem; border-radius:999px;"
                    f"background:{signature_color}20; color:{signature_color}; font-size:0.8rem; font-weight:700;'>"
                    f"{escape(selected_signature)}</div>"
                ),
                unsafe_allow_html=True,
            )
            st.caption(signature_label)

        st.markdown("##### Case Metrics")
        stat1, stat2, stat3, stat4 = st.columns(4)
        with stat1:
            st.metric(
                "Total orders",
                int(selected_row["total_orders"]),
                help="Source: order history for selected customer. Interpretation: customer activity base size.",
            )
        with stat2:
            st.metric(
                "Orders with claims",
                int(selected_row["orders_with_claims"]),
                help=(
                    "Calculation: count of orders containing missing items for selected customer. "
                    "Interpretation: claim recurrence signal."
                ),
            )
        with stat3:
            st.metric(
                "Claim rate",
                f"{selected_row['claim_rate']:.2f}%",
                help=(
                    "Calculation: items_reported_missing / (items_received + items_reported_missing) * 100. "
                    "Interpretation: intensity of claim behavior."
                ),
            )
        with stat4:
            st.metric(
                "Total spent",
                f"${selected_row['total_spent']:,.0f}",
                help=(
                    "Source: cumulative order_amount for selected customer. "
                    "Interpretation: business value and potential financial impact."
                ),
            )

        selected_orders = orders[orders["customer_id"] == selected_row["customer_id"]].copy()
        monthly = build_customer_monthly(selected_orders)
        links = build_driver_links(selected_orders, drivers, float(selected_row["risk_score"]))

    st.markdown("##### Case Evidence & Actions")
    st.markdown(
        "<div class='customer-section-subtitle'>Use these tabs to validate claim trend, inspect driver relationships, and simulate mitigation impact.</div>",
        unsafe_allow_html=True,
    )

    tab_timeline, tab_links, tab_actions = st.tabs(
        ["Claim Timeline", "Driver Links", "Action Simulator"]
    )

    with tab_timeline:
        st.markdown(
            "<div class='customer-section-subtitle'>Monthly claim orders and missing-rate trend versus portfolio baseline.</div>",
            unsafe_allow_html=True,
        )
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
                template="walmart_fraud",
                plot_bgcolor=COLORS['plot_bg'],
                paper_bgcolor=COLORS['paper_bg'],
                font_family=COLORS['font_family'],
                font_color="#1E293B",
                margin=dict(t=24, l=8, r=8, b=8),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    title=dict(font=dict(color="#334155")),
                ),
                yaxis=dict(
                    title=dict(text="Claim Orders", font=dict(color="#334155")),
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                ),
                yaxis2=dict(
                    title=dict(text="Claim Rate (%)", font=dict(color="#334155")),
                    overlaying="y",
                    side="right",
                    showgrid=False,
                    tickfont=dict(color="#334155"),
                ),
                hovermode="x unified",
            )
            st.plotly_chart(fig_timeline, use_container_width=True)

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
        st.markdown(
            "<div class='customer-section-subtitle'>Top driver links sorted by interaction volume and pair missing-rate.</div>",
            unsafe_allow_html=True,
        )
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
                template="walmart_fraud",
                plot_bgcolor=COLORS['plot_bg'],
                paper_bgcolor=COLORS['paper_bg'],
                font_family=COLORS['font_family'],
                font_color="#1E293B",
                margin=dict(t=10, l=8, r=8, b=8),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    title_text="Link Status",
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    title=dict(font=dict(color="#334155")),
                ),
                yaxis=dict(
                    showgrid=False,
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    title=dict(font=dict(color="#334155")),
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
            st.plotly_chart(fig_links, use_container_width=True)

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
                use_container_width=True,
                hide_index=True,
            )

    with tab_actions:
        if selected_row is None:
            st.info("Select an active case in Investigation Queue to run action simulation.")
        else:
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
                st.metric(
                    "Covered claims",
                    f"{coverage}%",
                    help=(
                        "Input parameter. Represents share of claims that would receive enhanced verification."
                    ),
                )
            with sim2:
                st.metric(
                    "Prevented items",
                    f"{prevented_items:.1f}",
                    help=(
                        "Calculation: items_reported_missing * verification_coverage * detection_lift. "
                        "Interpretation: expected avoided missing-item incidents."
                    ),
                )
            with sim3:
                st.metric(
                    "Potential savings",
                    f"${prevented_loss:,.0f}",
                    help=(
                        "Calculation: prevented_items * $15 loss proxy. "
                        "Interpretation: estimated savings under simulation assumptions."
                    ),
                )

    st.markdown("---")
    st.markdown("#### Exploratory Analysis")
    st.markdown(
        "<div class='customer-section-subtitle'>Use these views for broader segment diagnostics after case-level triage.</div>",
        unsafe_allow_html=True,
    )

    matrix_col, scatter_col = st.columns([1.15, 1.85])
    with matrix_col:
        st.markdown("##### Segment x Risk Matrix")
        st.markdown(
            "<div class='customer-section-subtitle'>Customer concentration by spending segment and risk tier.</div>",
            unsafe_allow_html=True,
        )
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
                template="walmart_fraud",
                plot_bgcolor=COLORS['plot_bg'],
                paper_bgcolor=COLORS['paper_bg'],
                font_family=COLORS['font_family'],
                font_color="#1E293B",
                margin=dict(t=12, r=8, b=8, l=8),
                xaxis=dict(showline=True, linecolor="#CBD5E1", tickfont=dict(color="#334155")),
                yaxis=dict(showline=True, linecolor="#CBD5E1", tickfont=dict(color="#334155")),
                coloraxis_colorbar=dict(
                    tickfont=dict(color="#334155"),
                    title=dict(text="Customers", font=dict(color="#334155")),
                ),
            )
            fig_matrix.update_traces(
                hovertemplate=(
                    "Segment: %{y}<br>"
                    "Risk: %{x}<br>"
                    "Customers: %{z}<extra></extra>"
                )
            )
            st.plotly_chart(fig_matrix, use_container_width=True)

    with scatter_col:
        st.markdown("##### Risk Concentration by Spend")
        st.markdown(
            "<div class='customer-section-subtitle'>Bubble size = order volume; guide lines show baseline and high-value threshold.</div>",
            unsafe_allow_html=True,
        )
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
                template="walmart_fraud",
                plot_bgcolor=COLORS['plot_bg'],
                paper_bgcolor=COLORS['paper_bg'],
                font_family=COLORS['font_family'],
                font_color="#1E293B",
                margin=dict(t=10, r=8, b=8, l=8),
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="left",
                    x=0,
                    title_text="Risk Tier",
                ),
                xaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    title=dict(font=dict(color="#334155")),
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor="#E2E8F0",
                    showline=True,
                    linecolor="#CBD5E1",
                    tickfont=dict(color="#334155"),
                    title=dict(font=dict(color="#334155")),
                ),
                hovermode="closest",
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
            st.plotly_chart(fig_scatter, use_container_width=True)


if __name__ == "__main__":
    main()

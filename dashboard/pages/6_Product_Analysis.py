"""
Product Analysis Page - Data quality first product intelligence dashboard.
"""
from __future__ import annotations

import sys
from datetime import date
from html import escape
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.viz_theme import CATEGORY_COLORS, PROJECT_THEME
from src.dashboard.components import COLORS, insight_card, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

st.set_page_config(
    page_title="Product Analysis - Walmart Fraud Detection",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
PRICE_BAND_BINS = [-np.inf, 10, 25, 50, 100, np.inf]
PRICE_BAND_LABELS = [
    "Budget (<$10)",
    "Core ($10-$25)",
    "Premium ($25-$50)",
    "High Value ($50-$100)",
    "Critical Value ($100+)",
]
MARGIN_BY_CATEGORY = {
    "Bakery": 0.24,
    "Beverages": 0.19,
    "Dairy": 0.18,
    "Electronics": 0.31,
    "Frozen": 0.22,
    "Household": 0.27,
    "Pantry": 0.21,
    "Personal Care": 0.33,
    "Produce": 0.26,
    "Snacks": 0.29,
    "Supermarket": 0.20,
}
BUSINESS_OWNER = "Fraud Ops Team"


def load_product_page_css() -> None:
    """Inject page-level styling aligned with dashboard design system."""
    st.markdown(
        """
        <style>
          .product-header {
            background: linear-gradient(135deg, #eff6ff 0%, #ffffff 65%);
            border: 1px solid #dbeafe;
            border-radius: 14px;
            padding: 1rem 1.15rem;
            box-shadow: var(--shadow-sm);
            margin-bottom: 0.95rem;
          }

          .product-header-main {
            display: flex;
            justify-content: space-between;
            gap: 0.9rem;
            align-items: flex-start;
            flex-wrap: wrap;
          }

          .product-header-title {
            margin: 0;
            color: var(--walmart-blue-dark);
            font-size: 2rem;
            font-weight: 800;
            letter-spacing: -0.02em;
          }

          .product-header-subtitle {
            color: var(--text-secondary);
            margin-top: 0.28rem;
            font-size: 0.92rem;
            max-width: 780px;
          }

          .product-header-meta {
            display: flex;
            gap: 0.38rem;
            flex-wrap: wrap;
            justify-content: flex-end;
          }

          .product-pill {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            border: 1px solid #dbeafe;
            background: #eff6ff;
            color: #1e3a8a;
            font-size: 0.72rem;
            font-weight: 700;
            padding: 0.12rem 0.52rem;
            white-space: nowrap;
          }

          .product-pill.warning {
            background: #ffedd5;
            border-color: #fdba74;
            color: #9a3412;
          }

          .product-pill.success {
            background: #dcfce7;
            border-color: #86efac;
            color: #166534;
          }

          .product-subtitle {
            color: #475569;
            font-size: 0.84rem;
            margin-top: -0.2rem;
            margin-bottom: 0.55rem;
          }

          .severity-legend {
            display: flex;
            gap: 0.35rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
          }

          .severity-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.1rem 0.5rem;
            font-size: 0.72rem;
            font-weight: 700;
            border: 1px solid transparent;
          }

          .severity-chip.critical {
            background: #fee2e2;
            border-color: #fca5a5;
            color: #991b1b;
          }

          .severity-chip.warning {
            background: #ffedd5;
            border-color: #fdba74;
            color: #9a3412;
          }

          .severity-chip.stable {
            background: #dcfce7;
            border-color: #86efac;
            color: #166534;
          }

          .scope-note {
            font-size: 0.8rem;
            color: #64748b;
            margin-top: 0.2rem;
          }

          .breadcrumb {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
            padding: 0.55rem 0.75rem;
            font-size: 0.8rem;
            color: #334155;
            margin-bottom: 0.75rem;
          }

          .data-lineage {
            border: 1px solid var(--border-light);
            border-radius: 12px;
            padding: 0.8rem 0.9rem;
            background: #ffffff;
            box-shadow: var(--shadow-sm);
          }

          .sku-queue-card {
            border: 1px solid #dbeafe;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: var(--shadow-sm);
            overflow: hidden;
            margin-bottom: 0.75rem;
          }

          .sku-queue-header {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            align-items: flex-start;
            flex-wrap: wrap;
            padding: 0.75rem 0.9rem;
            border-bottom: 1px solid #e2e8f0;
            background: #f8fafc;
          }

          .sku-queue-title {
            margin: 0;
            color: #0f172a;
            font-size: 0.9rem;
            font-weight: 800;
          }

          .sku-queue-subtitle {
            margin-top: 0.25rem;
            font-size: 0.78rem;
            color: #475569;
          }

          .sku-queue-legend {
            display: inline-flex;
            gap: 0.3rem;
            flex-wrap: wrap;
            justify-content: flex-end;
          }

          .sku-legend-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            font-size: 0.71rem;
            font-weight: 700;
            padding: 0.12rem 0.48rem;
            border: 1px solid transparent;
          }

          .sku-legend-chip.immediate {
            color: #991b1b;
            background: #fee2e2;
            border-color: #fca5a5;
          }

          .sku-legend-chip.fast-track {
            color: #9a3412;
            background: #ffedd5;
            border-color: #fdba74;
          }

          .sku-legend-chip.review {
            color: #1e3a8a;
            background: #dbeafe;
            border-color: #93c5fd;
          }

          .sku-legend-chip.monitor {
            color: #166534;
            background: #dcfce7;
            border-color: #86efac;
          }

          .sku-queue-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.79rem;
          }

          .sku-queue-table thead th {
            background: #f8fafc;
            color: #334155;
            font-size: 0.73rem;
            letter-spacing: 0.02em;
            font-weight: 700;
            padding: 0.55rem 0.6rem;
            border-bottom: 1px solid #e2e8f0;
            text-align: left;
            white-space: nowrap;
          }

          .sku-queue-table tbody td {
            padding: 0.52rem 0.6rem;
            border-bottom: 1px solid #edf2f7;
            color: #1e293b;
            vertical-align: middle;
          }

          .sku-queue-table tbody tr:nth-child(even) {
            background: #fbfdff;
          }

          .sku-queue-table tbody tr:hover {
            background: #eff6ff;
          }

          .sku-queue-table .num {
            text-align: right;
            font-variant-numeric: tabular-nums;
          }

          .sku-priority-chip,
          .sku-risk-chip {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 0.08rem 0.45rem;
            font-size: 0.69rem;
            font-weight: 800;
            border: 1px solid transparent;
            white-space: nowrap;
          }

          .sku-priority-chip.immediate,
          .sku-risk-chip.critical {
            color: #991b1b;
            background: #fee2e2;
            border-color: #fca5a5;
          }

          .sku-priority-chip.fast-track,
          .sku-risk-chip.high {
            color: #9a3412;
            background: #ffedd5;
            border-color: #fdba74;
          }

          .sku-priority-chip.review,
          .sku-risk-chip.medium {
            color: #1e3a8a;
            background: #dbeafe;
            border-color: #93c5fd;
          }

          .sku-priority-chip.monitor,
          .sku-risk-chip.low {
            color: #166534;
            background: #dcfce7;
            border-color: #86efac;
          }

          .sku-loss-flag {
            display: inline-flex;
            align-items: center;
            margin-left: 0.3rem;
            border-radius: 999px;
            padding: 0.06rem 0.4rem;
            font-size: 0.66rem;
            font-weight: 700;
            background: #fff7ed;
            color: #9a3412;
            border: 1px solid #fdba74;
            white-space: nowrap;
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


def _safe_ratio(numerator: float, denominator: float) -> float:
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def _safe_percent_change(current: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return float((current - baseline) / baseline * 100)


def _divide_series(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce").fillna(0.0)
    den = pd.to_numeric(denominator, errors="coerce").fillna(0.0)
    return pd.Series(np.where(den > 0, num / den, 0.0), index=num.index)


def build_category_color_map(categories: List[str]) -> Dict[str, str]:
    """Create consistent category color map using project tokens."""
    palette = PROJECT_THEME.get("categorical", [COLORS["walmart_blue"]])
    color_map: Dict[str, str] = {}
    fallback_idx = 0
    for category in categories:
        if category in CATEGORY_COLORS:
            color_map[category] = CATEGORY_COLORS[category]
            continue
        color_map[category] = palette[fallback_idx % len(palette)]
        fallback_idx += 1
    return color_map


def build_product_scope(products_df: pd.DataFrame, facts_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate product-level metrics for current page scope."""
    catalog = products_df[["product_id", "product_name", "category", "price"]].copy()
    catalog["price"] = pd.to_numeric(catalog["price"], errors="coerce").fillna(0.0)

    if facts_df.empty:
        scoped = catalog.copy()
        scoped["times_reported_missing"] = 0
        scoped["orders_affected"] = 0
        scoped["estimated_loss"] = 0.0
        scoped["unique_customers"] = 0
        scoped["unique_regions"] = 0
        scoped["anomaly_day_rate"] = 0.0
        scoped["anomaly_hour_rate"] = 0.0
        scoped["high_risk_region_rate"] = 0.0
        scoped["collusion_pair_rate"] = 0.0
        scoped["pattern_exposure_index"] = 0.0
    else:
        agg = (
            facts_df.groupby("product_id")
            .agg(
                times_reported_missing=("missing_item_id", "count"),
                orders_affected=("order_id", "nunique"),
                estimated_loss=("price", "sum"),
                unique_customers=("customer_id", "nunique"),
                unique_regions=("region", "nunique"),
                anomaly_day_rate=("is_anomaly_day", "mean"),
                anomaly_hour_rate=("is_anomaly_hour", "mean"),
                high_risk_region_rate=("is_high_risk_region", "mean"),
                collusion_pair_rate=("is_collusion_pair", "mean"),
                pattern_exposure_index=("pattern_exposure_points", "mean"),
            )
            .reset_index()
        )
        scoped = catalog.merge(agg, on="product_id", how="left")
        fill_numeric = [
            "times_reported_missing",
            "orders_affected",
            "estimated_loss",
            "unique_customers",
            "unique_regions",
            "anomaly_day_rate",
            "anomaly_hour_rate",
            "high_risk_region_rate",
            "collusion_pair_rate",
            "pattern_exposure_index",
        ]
        for col in fill_numeric:
            scoped[col] = pd.to_numeric(scoped[col], errors="coerce").fillna(0.0)

    scoped["avg_unit_price"] = np.where(
        scoped["times_reported_missing"] > 0,
        scoped["estimated_loss"] / scoped["times_reported_missing"],
        scoped["price"],
    )
    scoped["price_band"] = pd.cut(
        scoped["price"], bins=PRICE_BAND_BINS, labels=PRICE_BAND_LABELS
    ).astype(str)

    scoped["margin_rate"] = scoped["category"].map(MARGIN_BY_CATEGORY).fillna(0.22)
    scoped["margin_loss"] = scoped["estimated_loss"] * scoped["margin_rate"]
    scoped["replacement_cost"] = scoped["estimated_loss"] * 1.10

    turnover_rank = (
        scoped.groupby("category")["orders_affected"].rank(method="average", pct=True).fillna(0.0)
    )
    scoped["stock_turnover_proxy"] = turnover_rank * 100

    freq_max = max(float(scoped["times_reported_missing"].max()), 1.0)
    loss_max = max(float(scoped["estimated_loss"].max()), 1.0)
    margin_max = max(float(scoped["margin_rate"].max()), 0.01)
    pattern_max = max(float(scoped["pattern_exposure_index"].max()), 1.0)

    scoped["frequency_score"] = (scoped["times_reported_missing"] / freq_max * 100).clip(0, 100)
    scoped["value_score"] = (scoped["estimated_loss"] / loss_max * 100).clip(0, 100)
    scoped["margin_score"] = (scoped["margin_rate"] / margin_max * 100).clip(0, 100)
    scoped["pattern_score"] = (scoped["pattern_exposure_index"] / pattern_max * 100).clip(0, 100)

    scoped["risk_score"] = (
        scoped["frequency_score"] * 0.40
        + scoped["value_score"] * 0.30
        + scoped["margin_score"] * 0.20
        + scoped["pattern_score"] * 0.10
    ).clip(0, 100)

    scoped["risk_tier"] = pd.cut(
        scoped["risk_score"],
        bins=[-0.1, 30, 55, 75, 100],
        labels=["Low", "Medium", "High", "Critical"],
    ).astype(str)

    scoped["risk_rank"] = scoped["risk_score"].rank(method="dense", ascending=False).astype(int)

    scoped["prevention_cost"] = np.where(
        scoped["risk_tier"].isin(["High", "Critical"]),
        scoped["estimated_loss"] * 0.42,
        scoped["estimated_loss"] * 0.30,
    )
    scoped["prevention_roi"] = (
        _divide_series(scoped["replacement_cost"] - scoped["prevention_cost"], scoped["prevention_cost"]) * 100
    )

    scoped["opportunity_cost"] = scoped["estimated_loss"] * 1.25

    total_loss = float(scoped["estimated_loss"].sum())
    scoped["loss_pct_of_total"] = (
        _divide_series(scoped["estimated_loss"], pd.Series(total_loss, index=scoped.index)) * 100
    )

    return scoped.sort_values(["estimated_loss", "times_reported_missing"], ascending=False)


def build_category_scope(products_scope: pd.DataFrame, facts_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate category business and risk metrics for current scope."""
    category_scope = (
        products_scope.groupby("category")
        .agg(
            sku_count=("product_id", "nunique"),
            high_risk_skus=("risk_tier", lambda s: int(s.isin(["High", "Critical"]).sum())),
            times_reported_missing=("times_reported_missing", "sum"),
            estimated_loss=("estimated_loss", "sum"),
            margin_loss=("margin_loss", "sum"),
            replacement_cost=("replacement_cost", "sum"),
            prevention_cost=("prevention_cost", "sum"),
            avg_risk_score=("risk_score", "mean"),
        )
        .reset_index()
    )

    if not facts_df.empty:
        exposure = facts_df[["order_id", "category", "order_amount"]].drop_duplicates()
        revenue_proxy = exposure.groupby("category", as_index=False)["order_amount"].sum()
        revenue_proxy = revenue_proxy.rename(columns={"order_amount": "revenue_proxy"})
        category_scope = category_scope.merge(revenue_proxy, on="category", how="left")
    else:
        category_scope["revenue_proxy"] = 0.0

    category_scope["revenue_proxy"] = pd.to_numeric(
        category_scope["revenue_proxy"], errors="coerce"
    ).fillna(0.0)
    category_scope["loss_pct_revenue"] = (
        _divide_series(category_scope["estimated_loss"], category_scope["revenue_proxy"]) * 100
    )
    category_scope["prevention_roi"] = (
        _divide_series(
            category_scope["replacement_cost"] - category_scope["prevention_cost"],
            category_scope["prevention_cost"],
        )
        * 100
    )

    return category_scope.sort_values("estimated_loss", ascending=False)


def build_monthly_category_loss(facts_df: pd.DataFrame) -> pd.DataFrame:
    """Build monthly category trend table."""
    if facts_df.empty:
        return pd.DataFrame(
            columns=["month_start", "category", "estimated_loss", "missing_events", "month_label"]
        )

    monthly = facts_df.dropna(subset=["order_date"]).copy()
    monthly["month_start"] = monthly["order_date"].dt.to_period("M").dt.to_timestamp()

    monthly = (
        monthly.groupby(["month_start", "category"])
        .agg(
            estimated_loss=("price", "sum"),
            missing_events=("missing_item_id", "count"),
        )
        .reset_index()
        .sort_values("month_start")
    )
    monthly["month_label"] = monthly["month_start"].dt.strftime("%b %Y")
    return monthly


def build_loss_forecast(facts_df: pd.DataFrame) -> pd.DataFrame:
    """Build simple 30/60/90 days projected loss forecast using linear trend."""
    horizons = [30, 60, 90]
    if facts_df.empty:
        return pd.DataFrame({"horizon_days": horizons, "projected_loss": [0.0, 0.0, 0.0]})

    daily = facts_df.groupby("order_date")["price"].sum().sort_index()
    daily = daily.asfreq("D", fill_value=0.0)
    if len(daily) < 7:
        baseline = float(daily.mean()) if len(daily) else 0.0
        return pd.DataFrame(
            {
                "horizon_days": horizons,
                "projected_loss": [baseline * horizon for horizon in horizons],
            }
        )

    x = np.arange(len(daily), dtype=float)
    y = daily.values.astype(float)

    if np.allclose(y, y[0]):
        projections = [float(y.mean()) * horizon for horizon in horizons]
    else:
        slope, intercept = np.polyfit(x, y, 1)
        projections = []
        for horizon in horizons:
            future_x = np.arange(len(daily), len(daily) + horizon, dtype=float)
            pred = slope * future_x + intercept
            pred = np.clip(pred, a_min=0.0, a_max=None)
            projections.append(float(pred.sum()))

    return pd.DataFrame({"horizon_days": horizons, "projected_loss": projections})


def build_behavior_shift_table(facts_df: pd.DataFrame) -> pd.DataFrame:
    """Find products with significant changes between recent and baseline windows."""
    if facts_df.empty:
        return pd.DataFrame(columns=["product_id", "product_name", "baseline_loss", "recent_loss", "change_pct"])

    monthly = facts_df.dropna(subset=["order_date"]).copy()
    monthly["month_start"] = monthly["order_date"].dt.to_period("M").dt.to_timestamp()

    grouped = (
        monthly.groupby(["product_id", "product_name", "month_start"])["price"]
        .sum()
        .reset_index(name="monthly_loss")
    )

    shifts: List[Dict[str, Any]] = []
    for (product_id, product_name), frame in grouped.groupby(["product_id", "product_name"]):
        ordered = frame.sort_values("month_start")
        if len(ordered) < 4:
            continue
        recent = float(ordered.tail(3)["monthly_loss"].mean())
        baseline = float(ordered.iloc[:-3]["monthly_loss"].mean()) if len(ordered) > 3 else float(ordered.head(1)["monthly_loss"].mean())
        change_pct = _safe_percent_change(recent, baseline)
        shifts.append(
            {
                "product_id": product_id,
                "product_name": product_name,
                "baseline_loss": baseline,
                "recent_loss": recent,
                "change_pct": change_pct,
            }
        )

    shift_df = pd.DataFrame(shifts)
    if shift_df.empty:
        return shift_df

    shift_df["abs_change_pct"] = shift_df["change_pct"].abs()
    shift_df = shift_df.sort_values("abs_change_pct", ascending=False)
    return shift_df.drop(columns=["abs_change_pct"])


def compute_baseline_delta(monthly_df: pd.DataFrame) -> Tuple[float, float, float]:
    """Return baseline mean, recent mean, and percent delta."""
    if monthly_df.empty:
        return 0.0, 0.0, 0.0

    monthly_total = (
        monthly_df.groupby("month_start", as_index=False)["estimated_loss"].sum().sort_values("month_start")
    )
    if monthly_total.empty:
        return 0.0, 0.0, 0.0

    if len(monthly_total) < 4:
        baseline = float(monthly_total["estimated_loss"].mean())
        recent = float(monthly_total["estimated_loss"].tail(1).mean())
        delta_pct = _safe_percent_change(recent, baseline)
        return baseline, recent, delta_pct

    recent = float(monthly_total.tail(3)["estimated_loss"].mean())
    baseline = float(monthly_total.iloc[:-3]["estimated_loss"].mean())
    delta_pct = _safe_percent_change(recent, baseline)
    return baseline, recent, delta_pct


def build_model_accuracy_proxy(category_scope: pd.DataFrame, model_metrics: Dict[str, Any]) -> pd.DataFrame:
    """Create category-level model confidence proxy for product monitoring."""
    if category_scope.empty:
        return pd.DataFrame(columns=["category", "estimated_loss", "model_accuracy_proxy", "drift_status"])

    perf = model_metrics.get("performance", {})
    base_accuracy = 86.0 - abs(float(perf.get("rate_change_pct", 0.0))) * 0.1
    base_accuracy = float(np.clip(base_accuracy, 72.0, 94.0))

    loss_mean = float(category_scope["estimated_loss"].mean()) if len(category_scope) else 0.0
    loss_std = float(category_scope["estimated_loss"].std()) if len(category_scope) else 0.0

    drift_detected = any(d.get("is_drifting", False) for d in model_metrics.get("drift_analysis", []))

    proxy = category_scope[["category", "estimated_loss"]].copy()
    if loss_std > 0:
        z_score = (proxy["estimated_loss"] - loss_mean) / loss_std
    else:
        z_score = pd.Series(np.zeros(len(proxy)), index=proxy.index)

    proxy["model_accuracy_proxy"] = (base_accuracy - z_score * 2.5).clip(65.0, 96.0)
    proxy["drift_status"] = "Drift monitoring active" if drift_detected else "Stable"
    return proxy.sort_values("estimated_loss", ascending=False)


def build_knowledge_base_registry() -> pd.DataFrame:
    """List product-related knowledge assets and validation status."""
    root = Path(__file__).resolve().parents[2]
    registry = [
        {
            "asset": "notebooks/05_products_missing_items.ipynb",
            "scope": "Product EDA, risk scoring, product-driver/customer/region/time cross-analysis",
        },
        {
            "asset": "notebooks/06_dashboard_data_preparation.ipynb",
            "scope": "Dashboard-ready product summaries and metric contracts",
        },
        {
            "asset": "docs/DASHBOARD_ANALYSIS_REPORT.md",
            "scope": "Implemented product metrics and visualization inventory",
        },
        {
            "asset": "src/database/sql/002_create_views.sql",
            "scope": "Canonical product/category fraud views and SQL metric definitions",
        },
        {
            "asset": "src/etl/transformers.py",
            "scope": "Data quality transforms (produc_id normalization, typing, cleansing)",
        },
    ]

    rows = []
    for item in registry:
        exists = (root / item["asset"]).exists()
        rows.append(
            {
                "asset": item["asset"],
                "scope": item["scope"],
                "status": "Validated" if exists else "Missing",
            }
        )
    return pd.DataFrame(rows)


def build_consistency_checks(
    workspace: Dict[str, Any],
    products_scope: pd.DataFrame,
) -> pd.DataFrame:
    """Cross-page consistency checks for SKU/category integrity."""
    products = workspace["products"]
    missing_items = workspace["missing_items"]
    overview = workspace["overview_metrics"]
    regional = workspace["regional_summary"]

    overview_missing = int(overview.get("total_items_missing", 0))
    product_missing = int(products_scope["times_reported_missing"].sum())
    regional_missing = int(pd.to_numeric(regional["items_missing"], errors="coerce").fillna(0).sum())

    orphan_skus = sorted(set(missing_items["product_id"]) - set(products["product_id"]))
    missing_only_categories = sorted(
        set(missing_items["category"].dropna()) - set(products["category"].dropna())
    )

    checks = [
        {
            "check": "Total missing items parity (Overview vs Product page)",
            "status": "OK" if overview_missing == product_missing else "Mismatch",
            "detail": f"overview={overview_missing:,} | product={product_missing:,}",
        },
        {
            "check": "Total missing items parity (Regional vs Product page)",
            "status": "OK" if regional_missing == product_missing else "Mismatch",
            "detail": f"regional={regional_missing:,} | product={product_missing:,}",
        },
        {
            "check": "Orphan SKU references in missing items",
            "status": "OK" if len(orphan_skus) == 0 else "Gap",
            "detail": f"{len(orphan_skus)} orphan SKU IDs",
        },
        {
            "check": "Category consistency (catalog vs missing events)",
            "status": "OK" if len(missing_only_categories) == 0 else "Gap",
            "detail": f"{len(missing_only_categories)} categories only in missing events",
        },
    ]
    return pd.DataFrame(checks)


def build_automated_insights(
    products_scope: pd.DataFrame,
    category_scope: pd.DataFrame,
    facts_df: pd.DataFrame,
    baseline_delta_pct: float,
    temporal_summary: Dict[str, Any],
) -> List[str]:
    """Generate concise automated insights from current scope."""
    insights: List[str] = []
    if products_scope.empty:
        return insights

    total_loss = float(products_scope["estimated_loss"].sum())

    top_category_row = category_scope.iloc[0] if not category_scope.empty else None
    if top_category_row is not None and total_loss > 0:
        share = _safe_ratio(float(top_category_row["estimated_loss"]), total_loss) * 100
        insights.append(
            f"{top_category_row['category']} concentra {share:.1f}% da perda financeira estimada no escopo atual."
        )

    top_product = products_scope.iloc[0]
    insights.append(
        f"SKU de maior risco: {top_product['product_name']} (score {top_product['risk_score']:.1f}, perda ${top_product['estimated_loss']:,.0f})."
    )

    if not facts_df.empty and "spending_segment" in facts_df.columns:
        high_risk_products = products_scope[products_scope["risk_tier"].isin(["High", "Critical"])][
            "product_id"
        ]
        if len(high_risk_products) > 0:
            segment_slice = facts_df[facts_df["product_id"].isin(high_risk_products)]
            if not segment_slice.empty:
                segment_top = (
                    segment_slice.groupby("spending_segment", observed=False)["missing_item_id"]
                    .count()
                    .sort_values(ascending=False)
                    .head(1)
                )
                if not segment_top.empty:
                    seg_name = str(segment_top.index[0])
                    seg_share = _safe_ratio(float(segment_top.iloc[0]), float(segment_slice["missing_item_id"].count())) * 100
                    insights.append(
                        f"Segmento de cliente mais exposto entre SKUs de alto risco: {seg_name} ({seg_share:.1f}% dos eventos)."
                    )

    anomalies_total = int(temporal_summary.get("anomalies", {}).get("total", 0))
    trend = temporal_summary.get("trend", {})
    if anomalies_total > 0:
        worst_day = temporal_summary.get("patterns", {}).get("worst_day", "N/A")
        insights.append(
            f"Foram detectadas {anomalies_total} anomalias temporais; {worst_day} permanece como janela operacional critica."
        )

    insights.append(
        f"Perda media recente vs baseline historico: {baseline_delta_pct:+.1f}% (meses recentes contra historico anterior)."
    )

    return insights[:5]


def build_recommendations(
    products_scope: pd.DataFrame,
    category_scope: pd.DataFrame,
    forecast_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate top 3 actionable recommendations (impact x effort)."""
    total_high_risk_loss = float(
        products_scope[products_scope["risk_tier"].isin(["High", "Critical"])]["estimated_loss"].sum()
    )
    top_category = category_scope.iloc[0] if not category_scope.empty else None
    forecast_90 = float(
        forecast_df.loc[forecast_df["horizon_days"] == 90, "projected_loss"].iloc[0]
        if not forecast_df.empty and (forecast_df["horizon_days"] == 90).any()
        else 0.0
    )

    category_name = str(top_category["category"]) if top_category is not None else "Top category"
    category_loss = float(top_category["estimated_loss"]) if top_category is not None else 0.0

    actions = [
        {
            "action": "Reforcar prova de entrega nos 10 SKUs de maior risco",
            "impact_usd": total_high_risk_loss * 0.28,
            "effort": "Medium",
            "rationale": "Mitiga concentracao de perda em SKUs de alto score e alta recorrencia.",
        },
        {
            "action": f"Revisar processo operacional da categoria {category_name}",
            "impact_usd": category_loss * 0.22,
            "effort": "Low",
            "rationale": "Categoria lidera perda absoluta e risco composto no escopo analisado.",
        },
        {
            "action": "Ativar vigilancia reforcada para clusters regionais + clientes de risco",
            "impact_usd": forecast_90 * 0.16,
            "effort": "High",
            "rationale": "Alinha prevencao com previsao de perda 90 dias e sinais de anomalia temporal.",
        },
    ]

    rec_df = pd.DataFrame(actions)
    rec_df["impact_usd"] = pd.to_numeric(rec_df["impact_usd"], errors="coerce").fillna(0.0)
    rec_df = rec_df.sort_values("impact_usd", ascending=False)
    return rec_df.head(3)


def prepare_product_workspace(workspace: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare full-page datasets from cache workspace."""
    products = workspace["products"].copy()
    missing_items = workspace["missing_items"].copy()
    facts = workspace["missing_facts"].copy()
    customers = workspace["customer_summary"].copy()
    drivers = workspace["driver_summary"].copy()

    products["price"] = pd.to_numeric(products["price"], errors="coerce").fillna(0.0)
    facts["order_date"] = pd.to_datetime(facts["order_date"], errors="coerce")
    facts["price"] = pd.to_numeric(facts.get("price"), errors="coerce").fillna(0.0)
    facts["day_of_week"] = facts["order_date"].dt.day_name().fillna(facts.get("day_of_week"))
    facts["delivery_hour"] = pd.to_numeric(facts.get("delivery_hour"), errors="coerce")

    customer_cols = [
        col
        for col in [
            "customer_id",
            "risk_category",
            "spending_segment",
            "risk_score",
            "claim_rate",
            "total_spent",
            "total_orders",
        ]
        if col in customers.columns
    ]
    if customer_cols:
        customer_view = customers[customer_cols].copy()
        facts = facts.merge(customer_view, on="customer_id", how="left")

    driver_cols = [
        col
        for col in ["driver_id", "driver_name", "risk_category", "risk_score", "orders_completed"]
        if col in drivers.columns
    ]
    if driver_cols:
        driver_view = drivers[driver_cols].copy().rename(
            columns={
                "risk_category": "driver_risk_category",
                "risk_score": "driver_risk_score",
            }
        )
        facts = facts.merge(driver_view, on="driver_id", how="left")

    temporal = workspace["temporal_summary"]
    patterns = workspace["pattern_summary"]

    anomaly_details = temporal.get("anomalies", {}).get("details", {})
    anomaly_days = {
        str(item.get("day"))
        for item in anomaly_details.get("daily", [])
        if item.get("day") is not None
    }
    anomaly_hours = {
        int(item.get("hour"))
        for item in anomaly_details.get("hourly", [])
        if item.get("hour") is not None
    }

    high_risk_regions = {
        str(indicator.entity_id)
        for indicator in patterns.get("regional_patterns", [])
        if getattr(indicator, "entity_id", None) is not None
    }

    collusion_pairs = {
        f"{indicator.details.get('driver_id')}_{indicator.details.get('customer_id')}"
        for indicator in patterns.get("collusion_patterns", [])
        if isinstance(getattr(indicator, "details", None), dict)
        and indicator.details.get("driver_id") is not None
        and indicator.details.get("customer_id") is not None
    }

    facts["pair_key"] = facts["driver_id"].astype(str) + "_" + facts["customer_id"].astype(str)
    facts["is_anomaly_day"] = facts["day_of_week"].isin(anomaly_days)
    facts["is_anomaly_hour"] = (
        pd.to_numeric(facts["delivery_hour"], errors="coerce").fillna(-1).astype(int).isin(anomaly_hours)
    )
    facts["is_high_risk_region"] = facts["region"].isin(high_risk_regions)
    facts["is_collusion_pair"] = facts["pair_key"].isin(collusion_pairs)

    facts["pattern_exposure_points"] = (
        facts["is_anomaly_day"].astype(int) * 30
        + facts["is_anomaly_hour"].astype(int) * 25
        + facts["is_high_risk_region"].astype(int) * 25
        + facts["is_collusion_pair"].astype(int) * 20
    )

    products_scope_full = build_product_scope(products, facts)
    category_scope_full = build_category_scope(products_scope_full, facts)
    monthly_full = build_monthly_category_loss(facts)
    forecast_full = build_loss_forecast(facts)
    behavior_shift_full = build_behavior_shift_table(facts)

    consistency_df = build_consistency_checks(workspace, products_scope_full)

    return {
        "facts": facts,
        "products": products,
        "products_scope_full": products_scope_full,
        "category_scope_full": category_scope_full,
        "monthly_full": monthly_full,
        "forecast_full": forecast_full,
        "behavior_shift_full": behavior_shift_full,
        "consistency_df": consistency_df,
    }


def navigate_with_filters(target_page: str, params: Dict[str, str]) -> None:
    """Navigate to another page keeping scoped filters as query params."""
    st.query_params.clear()
    for key, value in params.items():
        if value:
            st.query_params[key] = value
    st.switch_page(target_page)


def build_sku_triage_queue(
    products_scope: pd.DataFrame,
    scoped_facts: pd.DataFrame,
    reference_date: pd.Timestamp,
) -> pd.DataFrame:
    """Build SKU triage queue with operational priority score and SLA targets."""
    if products_scope.empty:
        return pd.DataFrame(
            columns=[
                "product_id",
                "product_name",
                "category",
                "risk_tier",
                "risk_score",
                "estimated_loss",
                "times_reported_missing",
                "pattern_exposure_index",
                "loss_pct_of_total",
                "last_event_date",
                "recency_days",
                "recency_score",
                "loss_percentile",
                "priority_score",
                "priority_tier",
                "sla_target",
                "top_decile_flag",
                "last_event_label",
            ]
        )

    queue = products_scope.copy()
    queue["product_id"] = queue["product_id"].astype(str)
    queue["product_name"] = queue["product_name"].astype(str)
    queue["category"] = queue["category"].astype(str)

    numeric_cols = [
        "risk_score",
        "estimated_loss",
        "times_reported_missing",
        "pattern_exposure_index",
        "loss_pct_of_total",
    ]
    for col in numeric_cols:
        queue[col] = pd.to_numeric(queue.get(col), errors="coerce").fillna(0.0)

    event_max = pd.DataFrame(columns=["product_id", "last_event_date"])
    if not scoped_facts.empty and {"product_id", "order_date"}.issubset(scoped_facts.columns):
        event_slice = scoped_facts[["product_id", "order_date"]].copy()
        event_slice["order_date"] = pd.to_datetime(event_slice["order_date"], errors="coerce")
        event_slice = event_slice.dropna(subset=["order_date"])
        if not event_slice.empty:
            event_max = (
                event_slice.groupby("product_id", as_index=False)["order_date"]
                .max()
                .rename(columns={"order_date": "last_event_date"})
            )
            event_max["product_id"] = event_max["product_id"].astype(str)

    queue = queue.merge(event_max, on="product_id", how="left")
    queue["last_event_date"] = pd.to_datetime(queue["last_event_date"], errors="coerce")

    reference_ts = pd.to_datetime(reference_date, errors="coerce")
    if pd.isna(reference_ts):
        reference_ts = pd.Timestamp.now().normalize()
    else:
        reference_ts = reference_ts.normalize()

    queue["recency_days"] = np.where(
        queue["last_event_date"].notna(),
        (reference_ts - queue["last_event_date"].dt.normalize()).dt.days,
        999,
    )
    queue["recency_days"] = pd.to_numeric(queue["recency_days"], errors="coerce").fillna(999).clip(lower=0).astype(int)
    queue["recency_score"] = (100 - queue["recency_days"] * 3.33).clip(0, 100)
    queue["loss_percentile"] = queue["estimated_loss"].rank(method="average", pct=True).fillna(0.0) * 100

    queue["priority_score"] = (
        queue["risk_score"] * 0.60
        + queue["loss_percentile"] * 0.25
        + queue["recency_score"] * 0.15
    ).clip(0, 100)

    queue["priority_tier"] = np.select(
        [
            queue["priority_score"] >= 80,
            queue["priority_score"] >= 60,
            queue["priority_score"] >= 40,
        ],
        ["Immediate", "Fast Track", "Review"],
        default="Monitor",
    )

    sla_map = {
        "Immediate": "4h",
        "Fast Track": "12h",
        "Review": "24h",
        "Monitor": "48h",
    }
    queue["sla_target"] = queue["priority_tier"].map(sla_map).fillna("48h")

    top_decile_threshold = float(queue["estimated_loss"].quantile(0.90)) if len(queue) else 0.0
    queue["top_decile_flag"] = (queue["estimated_loss"] >= top_decile_threshold) & (queue["estimated_loss"] > 0)
    queue["last_event_label"] = queue["last_event_date"].dt.strftime("%Y-%m-%d").fillna("No events")

    return queue.sort_values(
        ["priority_score", "estimated_loss", "times_reported_missing"],
        ascending=[False, False, False],
    )


def render_sku_executive_queue(queue_df: pd.DataFrame, top_n: int) -> None:
    """Render compact executive queue with explicit severity labels and SLA."""
    if queue_df.empty:
        st.info("No SKU rows available for executive queue.")
        return

    top_queue = queue_df.head(top_n).copy()
    rows: List[str] = []
    for _, row in top_queue.iterrows():
        priority = str(row.get("priority_tier", "Monitor"))
        priority_css = priority.lower().replace(" ", "-")
        risk_tier = str(row.get("risk_tier", "Low"))
        risk_css = risk_tier.lower().replace(" ", "-")
        top_flag = (
            "<span class='sku-loss-flag'>Top 10%</span>"
            if bool(row.get("top_decile_flag", False))
            else ""
        )

        rows.append(
            "<tr>"
            f"<td>{escape(str(row.get('product_id', 'N/A')))}</td>"
            f"<td>{escape(str(row.get('product_name', 'N/A')))}</td>"
            f"<td>{escape(str(row.get('category', 'N/A')))}</td>"
            "<td>"
            f"<span class='sku-priority-chip {priority_css}'>{escape(priority)} · {float(row.get('priority_score', 0.0)):.1f}</span>"
            f"{top_flag}"
            "</td>"
            "<td>"
            f"<span class='sku-risk-chip {risk_css}'>{escape(risk_tier)}</span>"
            "</td>"
            f"<td class='num'>${float(row.get('estimated_loss', 0.0)):,.2f}</td>"
            f"<td class='num'>{int(float(row.get('times_reported_missing', 0.0))):,}</td>"
            f"<td class='num'>{float(row.get('pattern_exposure_index', 0.0)):.1f}</td>"
            f"<td class='num'>{escape(str(row.get('last_event_label', 'No events')))}</td>"
            f"<td class='num'>{escape(str(row.get('sla_target', '48h')))}</td>"
            "</tr>"
        )

    table_html = f"""
    <div class="sku-queue-card">
      <div class="sku-queue-header">
        <div>
          <p class="sku-queue-title">Executive SKU Queue</p>
          <div class="sku-queue-subtitle">
            Compact triage view with priority tier, explicit SLA, and top-loss flags.
          </div>
        </div>
        <div class="sku-queue-legend">
          <span class="sku-legend-chip immediate">Immediate · 4h</span>
          <span class="sku-legend-chip fast-track">Fast Track · 12h</span>
          <span class="sku-legend-chip review">Review · 24h</span>
          <span class="sku-legend-chip monitor">Monitor · 48h</span>
        </div>
      </div>
      <div style="overflow-x:auto;">
        <table class="sku-queue-table">
          <thead>
            <tr>
              <th>SKU</th>
              <th>Product</th>
              <th>Category</th>
              <th>Priority</th>
              <th>Risk Tier</th>
              <th class="num">Estimated Loss</th>
              <th class="num">Missing Events</th>
              <th class="num">Pattern Exposure</th>
              <th class="num">Last Event</th>
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


def build_sku_exploratory_view(queue_df: pd.DataFrame) -> pd.DataFrame:
    """Build exploration-friendly SKU table with operational columns."""
    if queue_df.empty:
        return pd.DataFrame(
            columns=[
                "SKU",
                "Product",
                "Category",
                "Priority",
                "Risk Tier",
                "Priority Score",
                "Risk Score",
                "Estimated Loss",
                "Missing Events",
                "Pattern Exposure",
                "SLA",
                "Gap",
                "Rate",
                "Volume",
                "Period",
                "Top Decile",
            ]
        )

    view = queue_df.copy()
    view["SLA"] = view["sla_target"].astype(str)
    view["Gap"] = (pd.to_numeric(view["priority_score"], errors="coerce").fillna(0.0) - pd.to_numeric(view["risk_score"], errors="coerce").fillna(0.0)).round(2)
    view["Rate"] = pd.to_numeric(view["loss_pct_of_total"], errors="coerce").fillna(0.0)
    view["Volume"] = pd.to_numeric(view["times_reported_missing"], errors="coerce").fillna(0).astype(int)
    view["Period"] = pd.to_datetime(view["last_event_date"], errors="coerce").dt.strftime("%Y-%m-%d").fillna("No events")
    view["Top Decile"] = np.where(view["top_decile_flag"], "Top 10%", "Standard")

    return view[
        [
            "product_id",
            "product_name",
            "category",
            "priority_tier",
            "risk_tier",
            "priority_score",
            "risk_score",
            "estimated_loss",
            "times_reported_missing",
            "pattern_exposure_index",
            "SLA",
            "Gap",
            "Rate",
            "Volume",
            "Period",
            "Top Decile",
        ]
    ].rename(
        columns={
            "product_id": "SKU",
            "product_name": "Product",
            "category": "Category",
            "priority_tier": "Priority",
            "risk_tier": "Risk Tier",
            "priority_score": "Priority Score",
            "risk_score": "Risk Score",
            "estimated_loss": "Estimated Loss",
            "times_reported_missing": "Missing Events",
            "pattern_exposure_index": "Pattern Exposure",
        }
    )


def main() -> None:
    render_sidebar()
    load_product_page_css()

    cache = get_default_cache()

    with st.spinner("Loading product intelligence workspace..."):
        workspace = cache.get_product_analysis_workspace()
        prepared = prepare_product_workspace(workspace)

    generated_at = pd.to_datetime(workspace.get("generated_at"), errors="coerce")
    generated_label = (
        generated_at.strftime("%Y-%m-%d %H:%M") if pd.notna(generated_at) else pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    )

    prefill_category = _query_param_value("product_category")
    prefill_product = _query_param_value("product_id")

    header_col, refresh_col = st.columns([6, 1])
    with header_col:
        st.markdown("### Operational Intelligence")
        st.markdown(
            f"""
            <div class="product-header">
              <div class="product-header-main">
                <div>
                  <h1 class="product-header-title">Product Analysis Control Tower</h1>
                  <div class="product-header-subtitle">
                    Product-level loss intelligence with data quality controls, cross-page consistency,
                    and SKU prioritization for fraud-loss mitigation.
                  </div>
                </div>
                <div class="product-header-meta">
                  <span class="product-pill success">System Status: Online</span>
                  <span class="product-pill">Last Updated: {generated_label}</span>
                  <span class="product-pill warning">Owner: {BUSINESS_OWNER}</span>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with refresh_col:
        st.markdown("<div style='height:1.6rem;'></div>", unsafe_allow_html=True)
        if st.button("Refresh Data", use_container_width=True):
            cache.refresh_all()
            st.cache_data.clear()
            st.rerun()

    facts = prepared["facts"]
    products = prepared["products"]

    available_categories = sorted([c for c in products["category"].dropna().astype(str).unique().tolist() if c])
    if prefill_category in available_categories:
        default_categories = [prefill_category]
    else:
        default_categories = available_categories

    date_min = facts["order_date"].min().date() if not facts.empty and facts["order_date"].notna().any() else date.today()
    date_max = facts["order_date"].max().date() if not facts.empty and facts["order_date"].notna().any() else date.today()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### Product Scope")
        selected_categories = st.multiselect(
            "Category",
            options=available_categories,
            default=default_categories,
        )

        selected_date_range = st.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )

        if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range
        elif isinstance(selected_date_range, list) and len(selected_date_range) == 2:
            start_date, end_date = selected_date_range[0], selected_date_range[1]
        else:
            start_date, end_date = date_min, date_max

        full_products = prepared["products_scope_full"]
        max_loss_value = float(full_products["estimated_loss"].max()) if not full_products.empty else 0.0
        loss_threshold = st.slider(
            "Loss Threshold (USD)",
            min_value=0,
            max_value=max(int(np.ceil(max_loss_value)), 100),
            value=min(100, max(int(np.ceil(max_loss_value)), 100)),
            step=10,
        )
        risk_threshold = st.slider("Composite Risk Threshold", min_value=0, max_value=100, value=60, step=5)
        st.caption("Filters apply to KPIs, charts, table, recommendations, and drill-down links.")

    st.markdown(
        "<div class='scope-note'>Lineage and cross-page consistency checks remain global; business and analytical metrics follow sidebar filters.</div>",
        unsafe_allow_html=True,
    )

    scoped_facts = facts.copy()
    if selected_categories:
        scoped_facts = scoped_facts[scoped_facts["category"].isin(selected_categories)]

    scoped_facts = scoped_facts[
        (scoped_facts["order_date"] >= pd.Timestamp(start_date))
        & (scoped_facts["order_date"] <= pd.Timestamp(end_date))
    ]

    scoped_products_catalog = products.copy()
    if selected_categories:
        scoped_products_catalog = scoped_products_catalog[
            scoped_products_catalog["category"].isin(selected_categories)
        ]

    products_scope = build_product_scope(scoped_products_catalog, scoped_facts)
    category_scope = build_category_scope(products_scope, scoped_facts)
    monthly_scope = build_monthly_category_loss(scoped_facts)
    forecast_scope = build_loss_forecast(scoped_facts)
    behavior_shift_scope = build_behavior_shift_table(scoped_facts)

    baseline_loss, recent_loss, baseline_delta_pct = compute_baseline_delta(monthly_scope)

    if products_scope.empty:
        st.info("No product data available for selected filters.")
        return

    categories_for_colors = category_scope["category"].dropna().astype(str).tolist()
    category_color_map = build_category_color_map(categories_for_colors)

    total_units_missing = int(scoped_facts["missing_item_id"].count())
    total_estimated_loss = float(scoped_facts["price"].sum()) if not scoped_facts.empty else 0.0
    high_risk_skus = int((products_scope["risk_score"] >= risk_threshold).sum())
    forecast_90 = float(
        forecast_scope.loc[forecast_scope["horizon_days"] == 90, "projected_loss"].iloc[0]
        if not forecast_scope.empty and (forecast_scope["horizon_days"] == 90).any()
        else 0.0
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        kpi_card(
            "Total Units Missing",
            f"{total_units_missing:,}",
            delta="Scoped missing-item events",
            color=COLORS["walmart_blue"],
        )
    with k2:
        kpi_card(
            "Total Estimated Loss",
            f"${total_estimated_loss:,.0f}",
            delta=f"Forecast 90d: ${forecast_90:,.0f}",
            color=COLORS["critical"],
        )
    with k3:
        kpi_card(
            "High-Risk SKUs",
            f"{high_risk_skus}",
            delta=f"Score >= {risk_threshold}",
            delta_color="inverse",
            color=COLORS["warning"],
        )
    with k4:
        delta_text = f"{baseline_delta_pct:+.1f}% vs baseline"
        kpi_card(
            "Loss Trend vs Baseline",
            f"${recent_loss:,.0f}",
            delta=delta_text,
            delta_color="inverse",
            color=COLORS["walmart_blue_light"],
        )

    st.markdown("---")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Treemap: Category > Price Band > SKU")
        st.markdown(
            "<div class='product-subtitle'>Node size = estimated loss; node color = composite risk score.</div>",
            unsafe_allow_html=True,
        )
        treemap_df = products_scope[products_scope["estimated_loss"] > 0].copy()
        if treemap_df.empty:
            st.info("No treemap data in selected scope.")
        else:
            fig_tree = px.treemap(
                treemap_df,
                path=["category", "price_band", "product_name"],
                values="estimated_loss",
                color="risk_score",
                color_continuous_scale="YlOrRd",
                hover_data={
                    "times_reported_missing": True,
                    "orders_affected": True,
                    "risk_tier": True,
                    "estimated_loss": ":.2f",
                    "risk_score": ":.1f",
                },
            )
            fig_tree.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                coloraxis_colorbar=dict(title="Risk"),
            )
            fig_tree.update_traces(
                hovertemplate=(
                    "Category: %{label}<br>"
                    "Loss: $%{value:,.2f}<br>"
                    "Risk: %{color:.1f}<extra></extra>"
                )
            )
            st.plotly_chart(fig_tree, use_container_width=True)

    with chart_col2:
        st.markdown("#### Time Series: Loss by Category (Last 6 Months)")
        st.markdown(
            "<div class='product-subtitle'>Dotted line marks historical baseline monthly loss.</div>",
            unsafe_allow_html=True,
        )
        if monthly_scope.empty:
            st.info("No temporal data in selected scope.")
        else:
            max_month = monthly_scope["month_start"].max()
            min_month = max_month - pd.DateOffset(months=5)
            monthly_recent = monthly_scope[monthly_scope["month_start"] >= min_month].copy()

            fig_ts = px.line(
                monthly_recent,
                x="month_start",
                y="estimated_loss",
                color="category",
                markers=True,
                color_discrete_map=category_color_map,
                hover_data={"missing_events": True, "estimated_loss": ":.2f"},
            )
            fig_ts.add_hline(
                y=baseline_loss,
                line_dash="dot",
                line_color=COLORS["warning"],
                annotation_text="Baseline",
            )
            fig_ts.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                yaxis_title="Estimated Loss (USD)",
                xaxis_title=None,
                legend_title_text="Category",
            )
            fig_ts.update_traces(
                hovertemplate=(
                    "Month: %{x|%b %Y}<br>"
                    "Category: %{fullData.name}<br>"
                    "Loss: $%{y:,.2f}<extra></extra>"
                )
            )
            st.plotly_chart(fig_ts, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### Heatmap: Product x Day of Week")
        st.markdown(
            "<div class='product-subtitle'>Top products by scoped loss reveal temporal concentration patterns.</div>",
            unsafe_allow_html=True,
        )

        if scoped_facts.empty:
            st.info("No heatmap data in selected scope.")
        else:
            top_products_ids = products_scope.head(12)["product_id"].tolist()
            heat = scoped_facts[scoped_facts["product_id"].isin(top_products_ids)].copy()
            heat["day_of_week"] = pd.Categorical(heat["day_of_week"], categories=DAY_ORDER, ordered=True)
            heat_data = (
                heat.groupby(["product_name", "day_of_week"], observed=False)["missing_item_id"]
                .count()
                .reset_index(name="missing_events")
            )
            heat_pivot = (
                heat_data.pivot(index="product_name", columns="day_of_week", values="missing_events")
                .fillna(0)
                .reindex(columns=DAY_ORDER)
            )

            if heat_pivot.empty:
                st.info("Not enough product/day combinations for heatmap.")
            else:
                fig_heat = px.imshow(
                    heat_pivot,
                    aspect="auto",
                    color_continuous_scale="OrRd",
                    labels={"x": "Day of Week", "y": "Product", "color": "Missing Events"},
                    text_auto=True,
                )
                fig_heat.update_layout(
                    template="walmart_fraud",
                    margin=dict(t=15, r=8, b=8, l=8),
                )
                st.plotly_chart(fig_heat, use_container_width=True)

    with chart_col4:
        st.markdown("#### Scatter: Unit Price x Missing Frequency")
        st.markdown(
            "<div class='product-subtitle'>Bubble size = financial loss; guide lines represent medians.</div>",
            unsafe_allow_html=True,
        )

        scatter_df = products_scope[products_scope["times_reported_missing"] > 0].copy()
        if scatter_df.empty:
            st.info("No scatter data in selected scope.")
        else:
            median_price = float(scatter_df["price"].median())
            median_freq = float(scatter_df["times_reported_missing"].median())

            fig_scatter = px.scatter(
                scatter_df,
                x="price",
                y="times_reported_missing",
                size="estimated_loss",
                color="category",
                color_discrete_map=category_color_map,
                hover_data={
                    "product_name": True,
                    "risk_score": ":.1f",
                    "pattern_exposure_index": ":.1f",
                    "estimated_loss": ":.2f",
                },
                opacity=0.82,
            )
            fig_scatter.add_vline(x=median_price, line_dash="dot", line_color=COLORS["warning"])
            fig_scatter.add_hline(y=median_freq, line_dash="dot", line_color=COLORS["warning"])
            fig_scatter.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis_title="Unit Price (USD)",
                yaxis_title="Missing Frequency",
                legend_title_text="Category",
            )
            fig_scatter.update_traces(
                hovertemplate=(
                    "SKU: %{customdata[0]}<br>"
                    "Price: $%{x:.2f}<br>"
                    "Missing events: %{y}<br>"
                    "Loss: $%{marker.size:,.2f}<br>"
                    "Risk score: %{customdata[1]:.1f}<extra></extra>"
                )
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    st.markdown("#### SKU Triage Workspace")
    st.markdown(
        "<div class='product-subtitle'>Hybrid triage flow: compact executive queue plus exploratory table with drill-down actions.</div>",
        unsafe_allow_html=True,
    )

    sku_queue = build_sku_triage_queue(
        products_scope=products_scope,
        scoped_facts=scoped_facts,
        reference_date=pd.Timestamp(end_date),
    )
    sku_queue = sku_queue[
        (sku_queue["estimated_loss"] >= float(loss_threshold))
        | (sku_queue["risk_score"] >= float(risk_threshold))
    ].copy()

    if sku_queue.empty:
        st.info("No SKU rows available for current scope and thresholds.")
    else:
        render_sku_executive_queue(sku_queue, top_n=12)

        c1, c2, c3, c4, c5 = st.columns([2.4, 1.3, 1.1, 1.4, 1.0])
        with c1:
            sku_search = st.text_input("Search SKU", placeholder="Product name or product ID")
        with c2:
            risk_tier_options = ["Critical", "High", "Medium", "Low"]
            queue_tiers = sku_queue["risk_tier"].dropna().astype(str).unique().tolist()
            selected_tiers = st.multiselect(
                "Risk Tier",
                options=[tier for tier in risk_tier_options if tier in queue_tiers],
                default=[tier for tier in risk_tier_options if tier in queue_tiers],
            )
        with c3:
            only_top_decile = st.toggle("Only top-decile loss", value=False)
        with c4:
            sort_by = st.selectbox(
                "Sort by",
                options=["Priority Score", "Estimated Loss", "Risk Score", "Missing Events"],
                index=0,
            )
        with c5:
            row_limit = st.selectbox("Row limit", options=[20, 50, 100], index=1)

        filtered_queue = sku_queue.copy()
        if sku_search:
            lookup = sku_search.strip().lower()
            filtered_queue = filtered_queue[
                filtered_queue["product_name"].astype(str).str.lower().str.contains(lookup, na=False)
                | filtered_queue["product_id"].astype(str).str.lower().str.contains(lookup, na=False)
            ]
        if selected_tiers:
            filtered_queue = filtered_queue[filtered_queue["risk_tier"].isin(selected_tiers)]
        if only_top_decile:
            filtered_queue = filtered_queue[filtered_queue["top_decile_flag"]]

        sort_map = {
            "Priority Score": "priority_score",
            "Estimated Loss": "estimated_loss",
            "Risk Score": "risk_score",
            "Missing Events": "times_reported_missing",
        }
        sort_col = sort_map[sort_by]
        filtered_queue = filtered_queue.sort_values(
            [sort_col, "estimated_loss", "times_reported_missing"],
            ascending=[False, False, False],
        )

        st.caption(f"Exploratory table rows: {min(len(filtered_queue), int(row_limit)):,} of {len(filtered_queue):,}.")
        exploratory_df = build_sku_exploratory_view(filtered_queue.head(int(row_limit)))

        with st.expander("Exploratory SKU Table", expanded=False):
            if exploratory_df.empty:
                st.info("No SKU rows after exploratory filters.")
            else:
                st.dataframe(
                    exploratory_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Priority Score": st.column_config.NumberColumn("Priority Score", format="%.1f"),
                        "Risk Score": st.column_config.NumberColumn("Risk Score", format="%.1f"),
                        "Estimated Loss": st.column_config.NumberColumn("Estimated Loss", format="$%.2f"),
                        "Missing Events": st.column_config.NumberColumn("Missing Events", format="%d"),
                        "Pattern Exposure": st.column_config.NumberColumn("Pattern Exposure", format="%.1f"),
                        "Gap": st.column_config.NumberColumn("Gap", format="%.2f"),
                        "Rate": st.column_config.NumberColumn("Rate", format="%.2f%%"),
                        "Volume": st.column_config.NumberColumn("Volume", format="%d"),
                    },
                )

        action_pool = filtered_queue if not filtered_queue.empty else sku_queue
        action_ids = action_pool["product_id"].astype(str).tolist()
        default_action_idx = action_ids.index(prefill_product) if prefill_product in action_ids else 0

        st.markdown("##### SKU Actions")
        selected_action_sku = st.selectbox(
            "Select SKU for drill-down",
            options=action_ids,
            index=default_action_idx,
            format_func=lambda pid: (
                f"{pid} - "
                f"{action_pool.loc[action_pool['product_id'].astype(str) == pid, 'product_name'].iloc[0]}"
            ),
        )

        selected_action_row = action_pool[action_pool["product_id"].astype(str) == selected_action_sku].iloc[0]
        selected_category = str(selected_action_row["category"])
        selected_name = str(selected_action_row["product_name"])

        st.markdown(
            (
                "<div class='breadcrumb'><strong>Breadcrumb:</strong> "
                f"Product ({escape(selected_name)}) -> Customers affected -> Geographic footprint -> Pattern diagnostics"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        n1, n2, n3 = st.columns(3)
        with n1:
            if st.button("Analyze Fraud Pattern", use_container_width=True):
                navigate_with_filters(
                    "pages/8_Patterns.py",
                    {
                        "product_id": selected_action_sku,
                        "product_category": selected_category,
                        "source_page": "product_analysis",
                    },
                )
        with n2:
            if st.button("Open Affected Customers", use_container_width=True):
                navigate_with_filters(
                    "pages/4_Customers.py",
                    {
                        "product_id": selected_action_sku,
                        "product_category": selected_category,
                        "source_page": "product_analysis",
                    },
                )
        with n3:
            if st.button("Open Geographic Footprint", use_container_width=True):
                navigate_with_filters(
                    "pages/5_Geographic.py",
                    {
                        "product_id": selected_action_sku,
                        "product_category": selected_category,
                        "source_page": "product_analysis",
                    },
                )

    st.markdown("---")

    st.markdown("#### Cross-Domain Product Relationships")
    tabs = st.tabs(
        [
            "Patterns",
            "Geographic",
            "Customers",
            "Drivers",
            "Model",
        ]
    )

    with tabs[0]:
        st.markdown(
            "<div class='product-subtitle'>Correlation between SKU exposure and pattern signals from temporal/network detectors.</div>",
            unsafe_allow_html=True,
        )

        corr_df = products_scope[["price", "times_reported_missing", "estimated_loss", "pattern_exposure_index"]].copy()
        corr_metrics = {
            "price_freq_corr": corr_df["price"].corr(corr_df["times_reported_missing"]),
            "freq_pattern_corr": corr_df["times_reported_missing"].corr(corr_df["pattern_exposure_index"]),
            "loss_pattern_corr": corr_df["estimated_loss"].corr(corr_df["pattern_exposure_index"]),
            "collusion_hit_rate": float(scoped_facts["is_collusion_pair"].mean() * 100) if not scoped_facts.empty else 0.0,
        }

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric("Price x Frequency Corr", f"{corr_metrics['price_freq_corr']:.2f}")
        with p2:
            st.metric("Frequency x Pattern Corr", f"{corr_metrics['freq_pattern_corr']:.2f}")
        with p3:
            st.metric("Loss x Pattern Corr", f"{corr_metrics['loss_pattern_corr']:.2f}")
        with p4:
            st.metric("Collusion Pair Hit Rate", f"{corr_metrics['collusion_hit_rate']:.1f}%")

        top_pattern = products_scope.nlargest(12, "pattern_exposure_index").copy()
        top_pattern = top_pattern[top_pattern["estimated_loss"] > 0]
        if top_pattern.empty:
            st.info("No pattern exposure events for selected scope.")
        else:
            fig_pattern = px.bar(
                top_pattern.sort_values("pattern_exposure_index"),
                x="pattern_exposure_index",
                y="product_name",
                orientation="h",
                color="category",
                color_discrete_map=category_color_map,
                hover_data={"estimated_loss": ":.2f", "risk_score": ":.1f"},
            )
            fig_pattern.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis_title="Pattern Exposure Index",
                yaxis_title=None,
            )
            st.plotly_chart(fig_pattern, use_container_width=True)

    with tabs[1]:
        st.markdown(
            "<div class='product-subtitle'>Top-5 products by loss distribution across regions from Geographic dataset.</div>",
            unsafe_allow_html=True,
        )

        top5_names = products_scope.head(5)["product_name"].tolist()
        geo_df = scoped_facts[scoped_facts["product_name"].isin(top5_names)].copy()
        if geo_df.empty:
            st.info("No regional product distribution for selected scope.")
        else:
            geo_agg = (
                geo_df.groupby(["region", "product_name"])
                .agg(estimated_loss=("price", "sum"), missing_events=("missing_item_id", "count"))
                .reset_index()
            )
            fig_geo = px.bar(
                geo_agg,
                x="region",
                y="estimated_loss",
                color="product_name",
                barmode="group",
                hover_data={"missing_events": True, "estimated_loss": ":.2f"},
            )
            fig_geo.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                yaxis_title="Estimated Loss (USD)",
                xaxis_title=None,
            )
            st.plotly_chart(fig_geo, use_container_width=True)

            geo_table = geo_agg.sort_values("estimated_loss", ascending=False).head(15)
            st.dataframe(
                geo_table.style.format({"estimated_loss": "${:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )

    with tabs[2]:
        st.markdown(
            "<div class='product-subtitle'>Customer segments associated with high-risk SKUs from Customers analytics.</div>",
            unsafe_allow_html=True,
        )

        if scoped_facts.empty or "spending_segment" not in scoped_facts.columns:
            st.info("Customer segment data unavailable for selected scope.")
        else:
            customer_matrix = (
                scoped_facts.groupby(["spending_segment", "risk_category"])
                .size()
                .reset_index(name="missing_events")
            )
            if customer_matrix.empty:
                st.info("No customer matrix rows for selected scope.")
            else:
                risk_order = ["Low", "Medium", "High", "Critical"]
                matrix = (
                    customer_matrix.pivot(index="spending_segment", columns="risk_category", values="missing_events")
                    .fillna(0)
                    .reindex(columns=risk_order)
                )
                fig_customer = px.imshow(
                    matrix,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="YlOrBr",
                    labels={"x": "Risk Category", "y": "Spending Segment", "color": "Missing Events"},
                )
                fig_customer.update_layout(template="walmart_fraud", margin=dict(t=15, r=8, b=8, l=8))
                st.plotly_chart(fig_customer, use_container_width=True)

            high_risk_products = products_scope[products_scope["risk_tier"].isin(["High", "Critical"])]["product_id"]
            customer_profile = scoped_facts[scoped_facts["product_id"].isin(high_risk_products)].copy()
            if not customer_profile.empty:
                profile = (
                    customer_profile.groupby("product_name")
                    .agg(
                        critical_customer_share=(
                            "risk_category",
                            lambda s: _safe_ratio(float(s.isin(["High", "Critical"]).sum()), float(len(s))) * 100,
                        ),
                        unique_customers=("customer_id", "nunique"),
                        estimated_loss=("price", "sum"),
                    )
                    .reset_index()
                    .sort_values("critical_customer_share", ascending=False)
                    .head(12)
                )
                st.dataframe(
                    profile.style.format(
                        {
                            "critical_customer_share": "{:.1f}%",
                            "estimated_loss": "${:,.2f}",
                        }
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

    with tabs[3]:
        st.markdown(
            "<div class='product-subtitle'>Top loss drivers per category linked from Drivers page metrics.</div>",
            unsafe_allow_html=True,
        )

        if scoped_facts.empty or "driver_name" not in scoped_facts.columns:
            st.info("Driver linkage data unavailable for selected scope.")
        else:
            driver_cat = (
                scoped_facts.groupby(["category", "driver_id", "driver_name"])
                .agg(missing_events=("missing_item_id", "count"), estimated_loss=("price", "sum"))
                .reset_index()
            )
            top_driver_cat = (
                driver_cat.sort_values(["category", "estimated_loss"], ascending=[True, False])
                .groupby("category")
                .head(1)
                .sort_values("estimated_loss", ascending=False)
            )
            if top_driver_cat.empty:
                st.info("No driver-category pattern for selected scope.")
            else:
                st.dataframe(
                    top_driver_cat.style.format({"estimated_loss": "${:,.2f}"}),
                    use_container_width=True,
                    hide_index=True,
                )

                fig_driver = px.bar(
                    top_driver_cat.sort_values("estimated_loss"),
                    x="estimated_loss",
                    y="category",
                    color="driver_name",
                    orientation="h",
                    hover_data={"missing_events": True},
                )
                fig_driver.update_layout(
                    template="walmart_fraud",
                    margin=dict(t=15, r=8, b=8, l=8),
                    xaxis_title="Estimated Loss (USD)",
                    yaxis_title=None,
                )
                st.plotly_chart(fig_driver, use_container_width=True)

    with tabs[4]:
        st.markdown(
            "<div class='product-subtitle'>Category-level model confidence proxy using global drift/performance signals.</div>",
            unsafe_allow_html=True,
        )

        model_proxy = build_model_accuracy_proxy(category_scope, workspace["model_metrics"])
        if model_proxy.empty:
            st.info("Model proxy table unavailable.")
        else:
            st.dataframe(
                model_proxy.style.format(
                    {
                        "estimated_loss": "${:,.2f}",
                        "model_accuracy_proxy": "{:.1f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

            fig_model = px.bar(
                model_proxy.sort_values("model_accuracy_proxy"),
                x="model_accuracy_proxy",
                y="category",
                color="estimated_loss",
                orientation="h",
                color_continuous_scale="Blues",
            )
            fig_model.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis_title="Model Accuracy Proxy (%)",
                yaxis_title=None,
            )
            st.plotly_chart(fig_model, use_container_width=True)

    st.markdown("---")

    st.markdown("#### Automated Insights and Significant Changes")
    insight_col, shift_col = st.columns([1.2, 1.8])

    with insight_col:
        insights = build_automated_insights(
            products_scope=products_scope,
            category_scope=category_scope,
            facts_df=scoped_facts,
            baseline_delta_pct=baseline_delta_pct,
            temporal_summary=workspace["temporal_summary"],
        )
        if insights:
            for line in insights:
                insight_card("Automated insight", line, icon="Signal", compact=True)
        else:
            st.info("No automated insights for selected scope.")

    with shift_col:
        st.markdown(
            "<div class='product-subtitle'>Products with largest relative change in loss behavior (recent window vs baseline).</div>",
            unsafe_allow_html=True,
        )

        if behavior_shift_scope.empty:
            st.info("No behavior-shift candidates for selected filters.")
        else:
            top_shift = behavior_shift_scope.head(12).copy()
            st.dataframe(
                top_shift.style.format(
                    {
                        "baseline_loss": "${:,.2f}",
                        "recent_loss": "${:,.2f}",
                        "change_pct": "{:+.1f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.markdown("---")

    st.markdown("#### Business Metrics and SKU Economics")
    overall_revenue = float(workspace["overview_metrics"].get("total_revenue", 0.0))
    loss_pct_revenue_total = _safe_ratio(total_estimated_loss, overall_revenue) * 100 if overall_revenue else 0.0
    margin_at_risk = float(products_scope["margin_loss"].sum())
    opportunity_cost = float(products_scope["opportunity_cost"].sum())

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        kpi_card("Loss as % Revenue", f"{loss_pct_revenue_total:.2f}%", delta="Scoped loss / total revenue", color=COLORS["critical"])
    with b2:
        kpi_card("Margin at Risk", f"${margin_at_risk:,.0f}", delta="Estimated margin exposure", color=COLORS["warning"])
    with b3:
        kpi_card("Opportunity Cost", f"${opportunity_cost:,.0f}", delta="Loss x 1.25 proxy", color=COLORS["walmart_blue"])
    with b4:
        kpi_card("Forecast 30/60/90", f"${forecast_90:,.0f}", delta="Projected 90-day loss", color=COLORS["walmart_blue_light"])

    biz_col1, biz_col2 = st.columns(2)

    with biz_col1:
        st.markdown("#### Margin x Loss at SKU Level")
        if products_scope.empty:
            st.info("No SKU economics data.")
        else:
            fig_margin = px.scatter(
                products_scope[products_scope["estimated_loss"] > 0],
                x="margin_rate",
                y="estimated_loss",
                size="risk_score",
                color="category",
                color_discrete_map=category_color_map,
                hover_data={
                    "product_name": True,
                    "stock_turnover_proxy": ":.1f",
                    "prevention_roi": ":.1f",
                    "risk_score": ":.1f",
                },
                opacity=0.8,
            )
            fig_margin.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis_title="Margin Rate",
                yaxis_title="Estimated Loss (USD)",
            )
            st.plotly_chart(fig_margin, use_container_width=True)

    with biz_col2:
        st.markdown("#### Replacement vs Prevention ROI by Category")
        if category_scope.empty:
            st.info("No category economics data.")
        else:
            roi_df = category_scope[["category", "replacement_cost", "prevention_cost", "prevention_roi"]].copy()
            fig_roi = px.bar(
                roi_df,
                x="category",
                y=["replacement_cost", "prevention_cost"],
                barmode="group",
                labels={"value": "USD", "variable": "Cost Type"},
            )
            fig_roi.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                xaxis_title=None,
                yaxis_title="Cost (USD)",
            )
            fig_roi.add_hline(
                y=float(roi_df["prevention_cost"].mean()),
                line_dash="dot",
                line_color=COLORS["warning"],
                annotation_text="Avg prevention cost",
            )
            st.plotly_chart(fig_roi, use_container_width=True)

            st.dataframe(
                roi_df.style.format(
                    {
                        "replacement_cost": "${:,.2f}",
                        "prevention_cost": "${:,.2f}",
                        "prevention_roi": "{:.1f}%",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )

    forecast_col, rec_col = st.columns([1.2, 1.8])
    with forecast_col:
        st.markdown("#### Forecast")
        fig_forecast = px.bar(
            forecast_scope,
            x="horizon_days",
            y="projected_loss",
            text="projected_loss",
            color="projected_loss",
            color_continuous_scale="Reds",
        )
        fig_forecast.update_traces(texttemplate="$%{text:,.0f}", textposition="outside")
        fig_forecast.update_layout(
            template="walmart_fraud",
            margin=dict(t=15, r=8, b=8, l=8),
            xaxis_title="Horizon (days)",
            yaxis_title="Projected Loss (USD)",
            showlegend=False,
        )
        st.plotly_chart(fig_forecast, use_container_width=True)

    with rec_col:
        st.markdown("#### Actionable Recommendations")
        rec_df = build_recommendations(products_scope, category_scope, forecast_scope)
        for idx, row in rec_df.reset_index(drop=True).iterrows():
            body = (
                f"Impact estimate: ${float(row['impact_usd']):,.0f}<br>"
                f"Effort: {row['effort']}<br>"
                f"{row['rationale']}"
            )
            insight_card(f"Action {idx + 1}", body, icon="Plan", compact=True)

    st.markdown("---")

    st.markdown("#### Data Lineage and Knowledge Base Validation")
    lineage_col1, lineage_col2 = st.columns(2)

    with lineage_col1:
        st.markdown("##### Knowledge Base Coverage")
        kb_df = build_knowledge_base_registry()
        st.dataframe(kb_df, use_container_width=True, hide_index=True)

    with lineage_col2:
        st.markdown("##### Source and Transformations")
        source_rows = []
        for source_name, meta in workspace.get("source_metadata", {}).items():
            source_rows.append(
                {
                    "source": source_name,
                    "table": meta.get("source", "N/A"),
                    "rows": meta.get("rows", 0),
                    "last_updated": meta.get("last_updated", "N/A"),
                    "transformations": " | ".join(meta.get("transformations", [])),
                }
            )
        source_df = pd.DataFrame(source_rows)
        if source_df.empty:
            st.info("No source metadata available.")
        else:
            st.dataframe(source_df, use_container_width=True, hide_index=True)

    st.markdown("##### Cross-Page Consistency Checks")
    st.dataframe(prepared["consistency_df"], use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()

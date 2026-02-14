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
import plotly.graph_objects as go
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
KPI_TOOLTIPS = {
    "loss_pct_revenue": (
        "Percentual da perda estimada sobre receita total do escopo filtrado. "
        "Calculado como: (Total Estimated Loss / Total Revenue) x 100"
    ),
    "margin_at_risk": (
        "Exposicao de margem baseada em loss estimado e margem media por categoria. "
        "Representa o impacto direto no lucro bruto"
    ),
    "opportunity_cost": (
        "Custo de oportunidade estimado usando multiplicador 1.25x sobre loss total. "
        "Considera impacto indireto em vendas perdidas"
    ),
    "forecast_306090": (
        "Projecao de perda para 30, 60 e 90 dias baseada em tendencia historica e sazonalidade"
    ),
}

CHART_TOOLTIPS = {
    "margin_loss_sku": (
        "Scatter mostrando relacao entre margem de lucro (%) e perda estimada ($) por SKU. "
        "Identifica produtos com maior impacto financeiro"
    ),
    "replacement_prevention_roi": (
        "Comparacao entre custo de reposicao de produtos perdidos vs investimento em prevencao por categoria. "
        "Linha tracejada mostra custo medio de prevencao"
    ),
    "forecast": (
        "Projecao linear de perda para proximos 30, 60 e 90 dias com valores especificos exibidos"
    ),
}

OPERATIONAL_KPI_TOOLTIPS = {
    "total_units_missing": (
        "Total de eventos de itens faltantes dentro do escopo filtrado de categoria e periodo."
    ),
    "total_estimated_loss": (
        "Soma do valor estimado perdido (price) para os eventos de missing item no escopo filtrado."
    ),
    "high_risk_skus": (
        "Quantidade de SKUs com score de risco acima do limite definido no filtro de risco composto."
    ),
    "loss_trend_baseline": (
        "Perda media recente comparada ao baseline historico. Delta indica variacao percentual versus periodo base."
    ),
}


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


def _percentile_rank(series: pd.Series, fallback: float = 50.0) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    if valid.nunique() <= 1:
        return pd.Series(np.full(len(values), fallback, dtype=float), index=values.index)
    return values.rank(method="average", pct=True).fillna(fallback / 100.0) * 100.0


def _safe_correlation(
    x: pd.Series,
    y: pd.Series,
    min_points: int = 8,
) -> Dict[str, Any]:
    pair = pd.DataFrame(
        {
            "x": pd.to_numeric(x, errors="coerce"),
            "y": pd.to_numeric(y, errors="coerce"),
        }
    ).dropna()

    sample_size = int(len(pair))
    if sample_size < min_points:
        return {"value": np.nan, "sample_size": sample_size, "status": "insufficient_sample"}
    if pair["x"].nunique() < 2 or pair["y"].nunique() < 2:
        return {"value": np.nan, "sample_size": sample_size, "status": "insufficient_variance"}
    return {"value": float(pair["x"].corr(pair["y"])), "sample_size": sample_size, "status": "ok"}


def _format_corr_value(value: float) -> str:
    return "N/A" if pd.isna(value) else f"{value:.2f}"


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


def build_scoped_revenue(facts_df: pd.DataFrame) -> float:
    """Compute scoped revenue from filtered facts using unique orders."""
    if facts_df.empty or "order_amount" not in facts_df.columns or "order_id" not in facts_df.columns:
        return 0.0

    revenue_base = facts_df[["order_id", "order_amount"]].copy()
    revenue_base["order_amount"] = pd.to_numeric(revenue_base["order_amount"], errors="coerce").fillna(0.0)
    revenue_base["order_id"] = revenue_base["order_id"].astype(str)
    return float(revenue_base.drop_duplicates(subset=["order_id"])["order_amount"].sum())


def build_margin_loss_plot_frame(products_scope: pd.DataFrame) -> pd.DataFrame:
    """Prepare clean and robust frame for Margin x Loss scatter."""
    expected_cols = [
        "product_id",
        "product_name",
        "category",
        "estimated_loss",
        "times_reported_missing",
        "risk_score",
        "margin_pct",
        "bubble_size",
    ]
    if products_scope.empty:
        return pd.DataFrame(columns=expected_cols)

    frame = products_scope.copy()
    frame["estimated_loss"] = pd.to_numeric(frame.get("estimated_loss"), errors="coerce").fillna(0.0)
    frame = frame[frame["estimated_loss"] > 0].copy()
    if frame.empty:
        return pd.DataFrame(columns=expected_cols)

    frame["times_reported_missing"] = pd.to_numeric(
        frame.get("times_reported_missing"), errors="coerce"
    ).fillna(0.0)
    frame["risk_score"] = pd.to_numeric(frame.get("risk_score"), errors="coerce").fillna(0.0)
    frame["margin_rate"] = pd.to_numeric(frame.get("margin_rate"), errors="coerce").fillna(0.0)
    frame["margin_pct"] = frame["margin_rate"] * 100.0

    frame["product_id"] = frame.get("product_id", pd.Series("", index=frame.index)).astype(str)
    frame["product_name"] = frame.get("product_name", pd.Series("", index=frame.index)).astype(str)
    frame["category"] = frame.get("category", pd.Series("Unknown", index=frame.index)).fillna("Unknown").astype(str)

    missing_min = float(frame["times_reported_missing"].min()) if not frame.empty else 0.0
    missing_max = float(frame["times_reported_missing"].max()) if not frame.empty else 0.0
    if missing_max > missing_min:
        frame["bubble_size"] = 10 + (
            (frame["times_reported_missing"] - missing_min) / (missing_max - missing_min)
        ) * 24
    else:
        frame["bubble_size"] = 16.0

    return frame[expected_cols].copy()


def build_loss_forecast(facts_df: pd.DataFrame) -> pd.DataFrame:
    """Build simple 30/60/90 days projected loss forecast using linear trend."""
    horizons = [30, 60, 90]
    if facts_df.empty:
        return pd.DataFrame(
            {
                "horizon_days": horizons,
                "projected_loss": [0.0, 0.0, 0.0],
                "projected_loss_low": [0.0, 0.0, 0.0],
                "projected_loss_high": [0.0, 0.0, 0.0],
            }
        )

    daily = facts_df.groupby("order_date")["price"].sum().sort_index()
    daily = daily.asfreq("D", fill_value=0.0)
    daily_std = float(daily.std(ddof=0)) if len(daily) > 1 else 0.0

    if len(daily) < 7:
        baseline = float(daily.mean()) if len(daily) else 0.0
        projections = [baseline * horizon for horizon in horizons]
        lower = [max(value - daily_std * np.sqrt(horizon), 0.0) for value, horizon in zip(projections, horizons)]
        upper = [value + daily_std * np.sqrt(horizon) for value, horizon in zip(projections, horizons)]
        return pd.DataFrame(
            {
                "horizon_days": horizons,
                "projected_loss": projections,
                "projected_loss_low": lower,
                "projected_loss_high": upper,
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

    lower = [max(value - daily_std * np.sqrt(horizon), 0.0) for value, horizon in zip(projections, horizons)]
    upper = [value + daily_std * np.sqrt(horizon) for value, horizon in zip(projections, horizons)]
    return pd.DataFrame(
        {
            "horizon_days": horizons,
            "projected_loss": projections,
            "projected_loss_low": lower,
            "projected_loss_high": upper,
        }
    )


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
    orders = workspace.get("orders", pd.DataFrame()).copy()
    products = workspace["products"].copy()
    missing_items = workspace["missing_items"].copy()
    facts = workspace["missing_facts"].copy()
    customers = workspace["customer_summary"].copy()
    drivers = workspace["driver_summary"].copy()

    products["price"] = pd.to_numeric(products["price"], errors="coerce").fillna(0.0)
    orders["order_date"] = pd.to_datetime(orders.get("order_date"), errors="coerce")
    orders["items_missing"] = pd.to_numeric(orders.get("items_missing"), errors="coerce").fillna(0.0)
    orders["items_delivered"] = pd.to_numeric(orders.get("items_delivered"), errors="coerce").fillna(0.0)
    orders["delivery_hour"] = pd.to_numeric(orders.get("delivery_hour"), errors="coerce").fillna(0).astype(int)
    if "day_of_week" in orders.columns:
        orders["day_of_week"] = orders["day_of_week"].fillna(orders["order_date"].dt.day_name())
    else:
        orders["day_of_week"] = orders["order_date"].dt.day_name()
    orders["region"] = orders.get("region", pd.Series(index=orders.index, dtype="object")).fillna("Unknown").astype(str)
    order_driver = (
        orders["driver_id"]
        if "driver_id" in orders.columns
        else pd.Series("", index=orders.index, dtype="object")
    )
    order_customer = (
        orders["customer_id"]
        if "customer_id" in orders.columns
        else pd.Series("", index=orders.index, dtype="object")
    )
    orders["pair_key"] = order_driver.astype(str) + "_" + order_customer.astype(str)
    orders["total_items"] = orders["items_delivered"] + orders["items_missing"]
    orders["order_missing_rate"] = np.where(
        orders["total_items"] > 0,
        orders["items_missing"] / orders["total_items"] * 100,
        0.0,
    )

    facts["order_date"] = pd.to_datetime(facts["order_date"], errors="coerce")
    facts["price"] = pd.to_numeric(facts.get("price"), errors="coerce").fillna(0.0)
    if "day_of_week" in facts.columns:
        facts["day_of_week"] = facts["day_of_week"].fillna(facts["order_date"].dt.day_name())
    else:
        facts["day_of_week"] = facts["order_date"].dt.day_name()
    facts["day_of_week"] = facts["day_of_week"].fillna("Unknown").astype(str)
    facts["delivery_hour"] = pd.to_numeric(facts.get("delivery_hour"), errors="coerce").fillna(-1).astype(int)
    facts["items_missing"] = pd.to_numeric(facts.get("items_missing"), errors="coerce").fillna(0.0)
    facts["items_delivered"] = pd.to_numeric(facts.get("items_delivered"), errors="coerce").fillna(0.0)
    facts["region"] = facts.get("region", pd.Series(index=facts.index, dtype="object")).fillna("Unknown").astype(str)

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

    day_rate_map: Dict[str, float] = {}
    hour_rate_map: Dict[int, float] = {}
    region_rate_map: Dict[str, float] = {}
    pair_rate_map: Dict[str, float] = {}
    pair_stats = pd.DataFrame(columns=["pair_key", "interactions", "pair_missing_rate"])
    global_missing_rate = 0.0

    if not orders.empty:
        global_missing_rate = float(pd.to_numeric(orders["order_missing_rate"], errors="coerce").fillna(0.0).mean())

        day_rates = (
            orders.groupby("day_of_week", observed=False)["order_missing_rate"]
            .mean()
            .dropna()
        )
        day_rate_map = {str(k): float(v) for k, v in day_rates.items()}

        hour_rates = (
            orders.groupby("delivery_hour", observed=False)["order_missing_rate"]
            .mean()
            .dropna()
        )
        hour_rate_map = {int(k): float(v) for k, v in hour_rates.items()}

        region_rates = (
            orders.groupby("region", observed=False)["order_missing_rate"]
            .mean()
            .dropna()
        )
        region_rate_map = {str(k): float(v) for k, v in region_rates.items()}

        pair_stats = (
            orders.groupby("pair_key", observed=False)
            .agg(
                interactions=("order_id", "count"),
                pair_missing_rate=("order_missing_rate", "mean"),
            )
            .reset_index()
        )
        if not pair_stats.empty:
            pair_stats["pair_missing_rate"] = pd.to_numeric(
                pair_stats["pair_missing_rate"], errors="coerce"
            ).fillna(0.0)
            pair_rate_map = {
                str(k): float(v)
                for k, v in pair_stats.set_index("pair_key")["pair_missing_rate"].items()
            }

    if not anomaly_days and day_rate_map:
        day_series = pd.Series(day_rate_map, dtype=float)
        day_cutoff = float(day_series.quantile(0.80))
        anomaly_days = set(day_series[day_series >= day_cutoff].index.astype(str).tolist())

    if not anomaly_hours and hour_rate_map:
        hour_series = pd.Series(hour_rate_map, dtype=float)
        hour_cutoff = float(hour_series.quantile(0.85))
        anomaly_hours = {
            int(idx)
            for idx in hour_series[hour_series >= hour_cutoff].index.tolist()
        }

    if not high_risk_regions and region_rate_map:
        region_series = pd.Series(region_rate_map, dtype=float)
        region_cutoff = float(region_series.quantile(0.85))
        high_risk_regions = set(
            region_series[region_series >= region_cutoff].index.astype(str).tolist()
        )

    if not collusion_pairs and not pair_stats.empty:
        pair_cutoff = float(pair_stats["pair_missing_rate"].quantile(0.95))
        fallback_collusion = pair_stats[
            (pair_stats["interactions"] >= 2)
            & (pair_stats["pair_missing_rate"] >= pair_cutoff)
            & (pair_stats["pair_missing_rate"] > 0)
        ]
        collusion_pairs = set(fallback_collusion["pair_key"].astype(str).tolist())

    facts["pair_key"] = facts["driver_id"].astype(str) + "_" + facts["customer_id"].astype(str)
    facts["is_anomaly_day"] = facts["day_of_week"].isin(anomaly_days)
    facts["is_anomaly_hour"] = facts["delivery_hour"].isin(anomaly_hours)
    facts["is_high_risk_region"] = facts["region"].isin(high_risk_regions)
    facts["is_collusion_pair"] = facts["pair_key"].isin(collusion_pairs)

    facts["day_missing_rate"] = pd.to_numeric(
        facts["day_of_week"].map(day_rate_map), errors="coerce"
    )
    facts["hour_missing_rate"] = pd.to_numeric(
        facts["delivery_hour"].map(hour_rate_map), errors="coerce"
    )
    facts["region_missing_rate"] = pd.to_numeric(
        facts["region"].map(region_rate_map), errors="coerce"
    )
    facts["pair_missing_rate"] = pd.to_numeric(
        facts["pair_key"].map(pair_rate_map), errors="coerce"
    )

    for col in [
        "day_missing_rate",
        "hour_missing_rate",
        "region_missing_rate",
        "pair_missing_rate",
    ]:
        facts[col] = pd.to_numeric(facts[col], errors="coerce").fillna(global_missing_rate)

    facts["day_signal"] = _percentile_rank(facts["day_missing_rate"])
    facts["hour_signal"] = _percentile_rank(facts["hour_missing_rate"])
    facts["region_signal"] = _percentile_rank(facts["region_missing_rate"])
    facts["pair_signal"] = _percentile_rank(facts["pair_missing_rate"])

    facts["pattern_exposure_points"] = (
        facts["day_signal"] * 0.30
        + facts["hour_signal"] * 0.20
        + facts["region_signal"] * 0.25
        + facts["pair_signal"] * 0.25
        + facts["is_anomaly_day"].astype(int) * 8
        + facts["is_anomaly_hour"].astype(int) * 7
        + facts["is_high_risk_region"].astype(int) * 7
        + facts["is_collusion_pair"].astype(int) * 10
    ).clip(0, 100)

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


@st.cache_data(ttl=480)  # 8-minute TTL for product analysis
def get_product_data():
    """
    Fetch product analysis workspace using lazy loading.
    This method uses an 8-minute TTL as product updates occur moderately frequently.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for product analysis page
    page_data = cache.get_page_data('product_analysis')

    # Extract product workspace from page data with explicit fallback diagnostics
    workspace = page_data.get('product_analysis_workspace')
    if workspace is None:
        error_detail = page_data.get('get_product_analysis_workspace_error')
        if error_detail:
            raise RuntimeError(
                f"Failed to load product analysis workspace: {error_detail}"
            )
        workspace = cache.get_product_analysis_workspace()

    return workspace


def main() -> None:
    render_sidebar()
    load_product_page_css()
    cache = get_default_cache()

    with st.spinner("Loading product intelligence workspace..."):
        workspace = get_product_data()
        prepared = prepare_product_workspace(workspace)

    prefill_category = _query_param_value("product_category")

    header_col, refresh_col = st.columns([6, 1])
    with header_col:
        st.markdown("### Operational Intelligence")
        st.markdown(
            """
            <div class="dashboard-header-row">
                <div>
                    <h1 style="margin:0; font-size: 2.5rem;">Product Analysis Control Tower</h1>
                    <p class="text-muted">Product-level loss intelligence with data quality controls, cross-page consistency, and SKU prioritization for fraud-loss mitigation.</p>
                </div>
                <div class="scope-badge-container">
                     <span class="badge badge-success">Product Scope</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with refresh_col:
        st.markdown("<div style='height:1.5rem;'></div>", unsafe_allow_html=True)
        if st.button("Refresh Data", use_container_width=True):
            cache.refresh_all()
            st.cache_data.clear()
            st.rerun()

    st.markdown("---")

    facts = prepared["facts"]
    products = prepared["products"]

    available_categories = sorted([c for c in products["category"].dropna().astype(str).unique().tolist() if c])
    if prefill_category in available_categories:
        default_categories = [prefill_category]
    else:
        default_categories = available_categories

    date_min = facts["order_date"].min().date() if not facts.empty and facts["order_date"].notna().any() else date.today()
    date_max = facts["order_date"].max().date() if not facts.empty and facts["order_date"].notna().any() else date.today()

    st.markdown("### Product Scope")
    scope_col1, scope_col2, scope_col3, scope_col4 = st.columns([2.2, 2.0, 1.6, 1.4])

    with scope_col1:
        selected_categories = st.multiselect(
            "Category",
            options=available_categories,
            default=default_categories,
        )
    with scope_col2:
        selected_date_range = st.date_input(
            "Date Range",
            value=(date_min, date_max),
            min_value=date_min,
            max_value=date_max,
        )
    with scope_col3:
        full_products = prepared["products_scope_full"]
        max_loss_value = float(full_products["estimated_loss"].max()) if not full_products.empty else 0.0
        loss_threshold = st.slider(
            "Loss Threshold (USD)",
            min_value=0,
            max_value=max(int(np.ceil(max_loss_value)), 100),
            value=min(100, max(int(np.ceil(max_loss_value)), 100)),
            step=10,
        )
    with scope_col4:
        risk_threshold = st.slider(
            "Composite Risk Threshold",
            min_value=0,
            max_value=100,
            value=60,
            step=5,
        )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
    elif isinstance(selected_date_range, list) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range[0], selected_date_range[1]
    else:
        start_date, end_date = date_min, date_max

    st.caption("Filters apply to KPIs, charts, tables, and recommendations.")

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
            tooltip=OPERATIONAL_KPI_TOOLTIPS["total_units_missing"],
        )
    with k2:
        kpi_card(
            "Total Estimated Loss",
            f"${total_estimated_loss:,.0f}",
            delta=f"Forecast 90d: ${forecast_90:,.0f}",
            color=COLORS["critical"],
            tooltip=OPERATIONAL_KPI_TOOLTIPS["total_estimated_loss"],
        )
    with k3:
        kpi_card(
            "High-Risk SKUs",
            f"{high_risk_skus}",
            delta=f"Score >= {risk_threshold}",
            delta_color="inverse",
            color=COLORS["warning"],
            tooltip=OPERATIONAL_KPI_TOOLTIPS["high_risk_skus"],
        )
    with k4:
        delta_text = f"{baseline_delta_pct:+.1f}% vs baseline"
        kpi_card(
            "Loss Trend vs Baseline",
            f"${recent_loss:,.0f}",
            delta=delta_text,
            delta_color="inverse",
            color=COLORS["walmart_blue_light"],
            tooltip=OPERATIONAL_KPI_TOOLTIPS["loss_trend_baseline"],
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
        "<div class='product-subtitle'>Hybrid triage flow: compact executive queue plus exploratory table for analyst deep dive.</div>",
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

    st.markdown("---")

    st.markdown("#### Cross-Domain Product Relationships")
    active_products_scope = products_scope[products_scope["times_reported_missing"] > 0].copy()
    if active_products_scope.empty:
        active_products_scope = products_scope[products_scope["estimated_loss"] > 0].copy()

    cross_domain_facts = scoped_facts.copy()
    if not active_products_scope.empty:
        active_ids = set(active_products_scope["product_id"].astype(str))
        cross_domain_facts = scoped_facts[
            scoped_facts["product_id"].astype(str).isin(active_ids)
        ].copy()

    tabs = st.tabs(["Patterns", "Geographic", "Customers", "Model"])

    with tabs[0]:
        st.markdown(
            "<div class='product-subtitle'>Correlation between SKU exposure and pattern signals from temporal/network detectors.</div>",
            unsafe_allow_html=True,
        )

        corr_pool = active_products_scope if not active_products_scope.empty else products_scope
        corr_df = corr_pool[
            ["price", "times_reported_missing", "estimated_loss", "pattern_exposure_index"]
        ].copy()
        corr_df = corr_df[pd.to_numeric(corr_df["times_reported_missing"], errors="coerce").fillna(0) > 0]

        price_freq = _safe_correlation(corr_df["price"], corr_df["times_reported_missing"])
        freq_pattern = _safe_correlation(
            corr_df["times_reported_missing"],
            corr_df["pattern_exposure_index"],
        )
        loss_pattern = _safe_correlation(
            corr_df["estimated_loss"],
            corr_df["pattern_exposure_index"],
        )

        collusion_base = (
            cross_domain_facts.drop_duplicates("order_id")
            if not cross_domain_facts.empty
            else pd.DataFrame()
        )
        collusion_hit_rate = (
            float(collusion_base["is_collusion_pair"].mean() * 100)
            if not collusion_base.empty and "is_collusion_pair" in collusion_base.columns
            else 0.0
        )

        p1, p2, p3, p4 = st.columns(4)
        with p1:
            st.metric(
                "Price x Frequency Corr",
                _format_corr_value(price_freq["value"]),
                help=(
                    "Pearson correlation between SKU unit price and missing-event frequency "
                    "for SKUs with at least one missing event."
                ),
            )
        with p2:
            st.metric(
                "Frequency x Pattern Corr",
                _format_corr_value(freq_pattern["value"]),
                help=(
                    "Pearson correlation between missing-event frequency and pattern exposure index. "
                    "Displays N/A when sample size or variance is insufficient."
                ),
            )
        with p3:
            st.metric(
                "Loss x Pattern Corr",
                _format_corr_value(loss_pattern["value"]),
                help=(
                    "Pearson correlation between estimated SKU loss and pattern exposure index. "
                    "Displays N/A when sample size or variance is insufficient."
                ),
            )
        with p4:
            st.metric(
                "Collusion Pair Hit Rate",
                f"{collusion_hit_rate:.1f}%",
                help=(
                    "Share of scoped orders linked to collusion-flagged driver-customer pairs."
                ),
            )

        st.caption(f"Correlation base: {len(corr_df):,} SKUs with missing events.")
        corr_status = [price_freq, freq_pattern, loss_pattern]
        if any(metric["status"] != "ok" for metric in corr_status):
            st.caption(
                "N/A values indicate insufficient sample size or no statistical variance after scope filters."
            )

        top_pattern = corr_pool[corr_pool["estimated_loss"] > 0].copy()
        if not top_pattern.empty:
            top_pattern = top_pattern.nlargest(12, "pattern_exposure_index")
        if top_pattern.empty:
            st.info("No pattern exposure events for selected scope.")
        else:
            if top_pattern["pattern_exposure_index"].nunique() <= 1:
                st.caption("Pattern exposure index has low variance in this scope; bars may appear flat.")
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

        geo_base = cross_domain_facts if not cross_domain_facts.empty else scoped_facts
        top5_ids = (active_products_scope if not active_products_scope.empty else products_scope).head(5)[
            "product_id"
        ].astype(str).tolist()
        geo_df = geo_base[geo_base["product_id"].astype(str).isin(top5_ids)].copy()
        if geo_df.empty and not geo_base.empty:
            fallback_ids = (
                geo_base.groupby("product_id")["price"]
                .sum()
                .sort_values(ascending=False)
                .head(5)
                .index.astype(str)
                .tolist()
            )
            geo_df = geo_base[geo_base["product_id"].astype(str).isin(fallback_ids)].copy()
        if geo_df.empty:
            st.info("No regional product distribution for selected scope.")
        else:
            geo_df["product_name"] = geo_df["product_name"].fillna(geo_df["product_id"].astype(str))
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

        customer_base = cross_domain_facts if not cross_domain_facts.empty else scoped_facts
        if customer_base.empty or "spending_segment" not in customer_base.columns:
            st.info("Customer segment data unavailable for selected scope.")
        else:
            customer_matrix = (
                customer_base.dropna(subset=["spending_segment", "risk_category"])
                .groupby(["spending_segment", "risk_category"], observed=False)
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

            risk_pool = active_products_scope if not active_products_scope.empty else products_scope
            high_risk_products = risk_pool[risk_pool["risk_tier"].isin(["High", "Critical"])]["product_id"]
            if len(high_risk_products) == 0 and not risk_pool.empty:
                threshold = float(risk_pool["risk_score"].quantile(0.80))
                high_risk_products = risk_pool[risk_pool["risk_score"] >= threshold]["product_id"]

            customer_profile = customer_base[
                customer_base["product_id"].astype(str).isin(high_risk_products.astype(str))
            ].copy()
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
            else:
                st.info("No customer profile rows linked to high-risk SKUs in current scope.")

    with tabs[3]:
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
    scoped_revenue = build_scoped_revenue(scoped_facts)
    loss_pct_revenue_total = _safe_ratio(total_estimated_loss, scoped_revenue) * 100 if scoped_revenue else 0.0
    margin_at_risk = float(products_scope["margin_loss"].sum())
    opportunity_cost = float(products_scope["opportunity_cost"].sum())
    forecast_lookup = (
        forecast_scope.set_index("horizon_days")["projected_loss"].to_dict()
        if not forecast_scope.empty
        else {}
    )
    forecast_30 = float(forecast_lookup.get(30, 0.0))
    forecast_60 = float(forecast_lookup.get(60, 0.0))

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        kpi_card(
            "Loss as % Revenue",
            f"{loss_pct_revenue_total:.2f}%",
            delta=f"Loss ${total_estimated_loss:,.0f} / Revenue ${scoped_revenue:,.0f}",
            color=COLORS["critical"],
            tooltip=KPI_TOOLTIPS["loss_pct_revenue"],
        )
    with b2:
        kpi_card(
            "Margin at Risk",
            f"${margin_at_risk:,.0f}",
            delta="Estimated margin exposure",
            color=COLORS["warning"],
            tooltip=KPI_TOOLTIPS["margin_at_risk"],
        )
    with b3:
        kpi_card(
            "Opportunity Cost",
            f"${opportunity_cost:,.0f}",
            delta="Loss x 1.25 proxy",
            color=COLORS["walmart_blue"],
            tooltip=KPI_TOOLTIPS["opportunity_cost"],
        )
    with b4:
        kpi_card(
            "Forecast 30/60/90",
            f"${forecast_90:,.0f}",
            delta=f"30d ${forecast_30:,.0f} | 60d ${forecast_60:,.0f}",
            color=COLORS["walmart_blue_light"],
            tooltip=KPI_TOOLTIPS["forecast_306090"],
        )
    st.caption(
        "Consistency check: Total Estimated Loss and Forecast 90d reuse the same scoped base as Operational Intelligence; "
        "all KPIs/charts in this section follow Product Scope filters."
    )

    biz_col1, biz_col2 = st.columns(2)

    with biz_col1:
        st.markdown(
            "#### Margin x Loss at SKU Level "
            f"<span title=\"{escape(CHART_TOOLTIPS['margin_loss_sku'], quote=True)}\">ℹ️</span>",
            unsafe_allow_html=True,
        )
        if products_scope.empty:
            st.info("No SKU economics data.")
        else:
            margin_df = build_margin_loss_plot_frame(products_scope)
            if margin_df.empty:
                st.info("No SKU economics data.")
            else:
                control_col1, control_col2 = st.columns([1, 1])
                with control_col1:
                    top_n = st.slider(
                        "Top SKUs destacados",
                        min_value=5,
                        max_value=15,
                        value=8,
                        step=1,
                        key="margin_loss_top_n",
                    )
                with control_col2:
                    highlight_focus = st.toggle(
                        "Destacar apenas Electronics e Supermarket",
                        value=True,
                        key="margin_loss_focus_toggle",
                    )

                top_loss_ids = set(margin_df.nlargest(int(top_n), "estimated_loss")["product_id"].astype(str))
                margin_df["is_top_sku"] = margin_df["product_id"].astype(str).isin(top_loss_ids)
                margin_df["is_focus_category"] = margin_df["category"].isin(["Electronics", "Supermarket"])
                margin_df["sku_label"] = np.where(margin_df["is_top_sku"], margin_df["product_name"], "")

                positive_losses = margin_df["estimated_loss"][margin_df["estimated_loss"] > 0]
                min_positive_loss = float(positive_losses.min()) if not positive_losses.empty else 0.0
                max_loss = float(positive_losses.max()) if not positive_losses.empty else 0.0
                dispersion_ratio = max_loss / max(min_positive_loss, 1e-9) if max_loss > 0 else 0.0
                use_log_y = bool(len(positive_losses) >= 10 and dispersion_ratio >= 20)
                scale_label = (
                    "Escala logaritmica para melhorar comparabilidade."
                    if use_log_y
                    else "Escala linear."
                )
                st.markdown(
                    (
                        "<div class='product-subtitle'>"
                        f"Quadrante superior direito concentra maior impacto financeiro; labels mostram Top {int(top_n)} SKUs por loss. "
                        f"{scale_label}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )

                avg_margin_pct = float(margin_df["margin_pct"].mean()) if not margin_df.empty else 0.0
                avg_loss = float(margin_df["estimated_loss"].mean()) if not margin_df.empty else 0.0

                fig_margin = px.scatter(
                    margin_df,
                    x="margin_pct",
                    y="estimated_loss",
                    size="bubble_size",
                    color="category",
                    color_discrete_map=category_color_map,
                    hover_data={
                        "product_id": True,
                        "product_name": True,
                        "category": True,
                        "margin_pct": ":.1f",
                        "estimated_loss": ":.2f",
                        "times_reported_missing": ":.0f",
                        "risk_score": ":.1f",
                        "bubble_size": False,
                        "is_top_sku": False,
                        "is_focus_category": False,
                        "sku_label": False,
                    },
                    opacity=0.45,
                    log_y=use_log_y,
                )

                top_df = margin_df[margin_df["is_top_sku"]].copy()
                if not top_df.empty:
                    fig_margin.add_trace(
                        go.Scatter(
                            x=top_df["margin_pct"],
                            y=top_df["estimated_loss"],
                            mode="markers+text",
                            text=top_df["sku_label"],
                            textposition="top center",
                            showlegend=False,
                            marker=dict(
                                size=top_df["bubble_size"].tolist(),
                                color=[
                                    category_color_map.get(cat, COLORS["walmart_blue_light"])
                                    for cat in top_df["category"].tolist()
                                ],
                                line=dict(width=2, color="#0f172a"),
                                opacity=0.9,
                            ),
                            customdata=np.stack(
                                [
                                    top_df["product_id"].to_numpy(),
                                    top_df["product_name"].to_numpy(),
                                    top_df["category"].to_numpy(),
                                    top_df["times_reported_missing"].to_numpy(),
                                    top_df["risk_score"].to_numpy(),
                                ],
                                axis=-1,
                            ),
                            hovertemplate=(
                                "SKU: %{customdata[0]}<br>"
                                "Product: %{customdata[1]}<br>"
                                "Category: %{customdata[2]}<br>"
                                "Margin: %{x:.1f}%<br>"
                                "Loss: $%{y:,.2f}<br>"
                                "Missing events: %{customdata[3]:.0f}<br>"
                                "Risk score: %{customdata[4]:.1f}<extra></extra>"
                            ),
                        )
                    )

                for trace in fig_margin.data:
                    if not trace.showlegend:
                        continue
                    base_opacity = 0.45
                    if highlight_focus and trace.name not in ["Electronics", "Supermarket"]:
                        trace.opacity = 0.2
                    else:
                        trace.opacity = base_opacity
                    trace.marker.line = dict(width=0.6, color="#ffffff")

                fig_margin.update_traces(textposition="top center")
                fig_margin.add_vline(
                    x=avg_margin_pct,
                    line_dash="dot",
                    line_color=COLORS["warning"],
                    annotation_text="Avg margin",
                )
                fig_margin.add_hline(
                    y=avg_loss,
                    line_dash="dot",
                    line_color=COLORS["critical"],
                    annotation_text="Avg loss",
                )
                fig_margin.update_layout(
                    template="walmart_fraud",
                    margin=dict(t=15, r=8, b=8, l=8),
                    xaxis_title="Margin Rate (%)",
                    yaxis_title="Estimated Loss (USD)",
                    legend_title_text="Category",
                    hovermode="closest",
                    uniformtext_minsize=8,
                )
                st.plotly_chart(fig_margin, use_container_width=True)

    with biz_col2:
        st.markdown(
            "#### Replacement vs Prevention ROI by Category "
            f"<span title=\"{escape(CHART_TOOLTIPS['replacement_prevention_roi'], quote=True)}\">ℹ️</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='product-subtitle'>Compare custo de reposicao vs prevencao e priorize categorias com maior economia potencial.</div>",
            unsafe_allow_html=True,
        )
        if category_scope.empty:
            st.info("No category economics data.")
        else:
            roi_df = category_scope[["category", "replacement_cost", "prevention_cost", "prevention_roi"]].copy()
            roi_df["potential_savings_usd"] = (
                pd.to_numeric(roi_df["replacement_cost"], errors="coerce").fillna(0.0)
                - pd.to_numeric(roi_df["prevention_cost"], errors="coerce").fillna(0.0)
            )
            roi_df["potential_savings_pct"] = (
                _divide_series(roi_df["potential_savings_usd"], roi_df["replacement_cost"]) * 100
            )
            roi_df = roi_df.sort_values("potential_savings_usd", ascending=False)
            roi_df["opportunity_flag"] = (
                pd.to_numeric(roi_df["replacement_cost"], errors="coerce").fillna(0.0)
                >= pd.to_numeric(roi_df["prevention_cost"], errors="coerce").fillna(0.0) * 1.5
            )
            replacement_colors = [
                COLORS["critical"] if flag else COLORS["walmart_blue_light"]
                for flag in roi_df["opportunity_flag"].tolist()
            ]

            fig_roi = go.Figure()
            fig_roi.add_trace(
                go.Bar(
                    name="Replacement Cost",
                    x=roi_df["category"],
                    y=roi_df["replacement_cost"],
                    marker_color=replacement_colors,
                    text=[f"${value:,.0f}" for value in roi_df["replacement_cost"].tolist()],
                    textposition="outside",
                    hovertemplate="Category: %{x}<br>Replacement: $%{y:,.2f}<extra></extra>",
                )
            )
            fig_roi.add_trace(
                go.Bar(
                    name="Prevention Cost",
                    x=roi_df["category"],
                    y=roi_df["prevention_cost"],
                    marker_color=COLORS["warning"],
                    text=[f"${value:,.0f}" for value in roi_df["prevention_cost"].tolist()],
                    textposition="outside",
                    hovertemplate="Category: %{x}<br>Prevention: $%{y:,.2f}<extra></extra>",
                )
            )
            for _, row in roi_df.iterrows():
                y_anchor = max(float(row["replacement_cost"]), float(row["prevention_cost"])) * 1.08
                fig_roi.add_annotation(
                    x=row["category"],
                    y=y_anchor,
                    text=f"{float(row['potential_savings_pct']):.0f}% savings",
                    showarrow=False,
                    font=dict(size=10, color="#334155"),
                )
            fig_roi.update_layout(
                template="walmart_fraud",
                margin=dict(t=15, r=8, b=8, l=8),
                barmode="group",
                xaxis_title=None,
                yaxis_title="Cost (USD)",
                legend_title_text="Cost Type",
            )
            avg_prevention_cost = float(roi_df["prevention_cost"].mean()) if not roi_df.empty else 0.0
            if avg_prevention_cost > 0:
                fig_roi.add_hline(
                    y=avg_prevention_cost,
                    line_dash="dot",
                    line_color=COLORS["warning"],
                    annotation_text="Avg prevention cost",
                )
            st.plotly_chart(fig_roi, use_container_width=True)

    forecast_col, rec_col = st.columns([1.2, 1.8])
    with forecast_col:
        st.markdown(
            "#### Forecast: Historical Context + 30/60/90 Projection "
            f"<span title=\"{escape(CHART_TOOLTIPS['forecast'], quote=True)}\">ℹ️</span>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='product-subtitle'>Linha azul = historico acumulado (60 dias), vermelho = projecao com faixa min/max e baseline esperado.</div>",
            unsafe_allow_html=True,
        )
        daily_loss = (
            scoped_facts.dropna(subset=["order_date"])
            .groupby("order_date")["price"]
            .sum()
            .sort_index()
            .asfreq("D", fill_value=0.0)
            if not scoped_facts.empty
            else pd.Series(dtype=float)
        )
        hist_60 = daily_loss.tail(60)
        hist_60_cum = hist_60.cumsum() if not hist_60.empty else pd.Series(dtype=float)
        last_date = hist_60.index.max() if not hist_60.empty else pd.Timestamp(end_date)

        forecast_plot = forecast_scope.copy()
        forecast_plot["forecast_date"] = forecast_plot["horizon_days"].apply(
            lambda horizon: last_date + pd.Timedelta(days=int(horizon))
        )
        daily_baseline = float(daily_loss.mean()) if not daily_loss.empty else 0.0
        forecast_plot["baseline_target"] = forecast_plot["horizon_days"] * daily_baseline

        fig_forecast = go.Figure()
        if not hist_60_cum.empty:
            fig_forecast.add_trace(
                go.Scatter(
                    x=hist_60_cum.index,
                    y=hist_60_cum.values,
                    mode="lines",
                    name="Historical cumulative loss (last 60d)",
                    line=dict(color=COLORS["walmart_blue_light"], width=2),
                    hovertemplate="%{x|%Y-%m-%d}<br>Historical cumulative: $%{y:,.2f}<extra></extra>",
                )
            )

        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_plot["forecast_date"],
                y=forecast_plot["projected_loss_high"],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip",
            )
        )
        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_plot["forecast_date"],
                y=forecast_plot["projected_loss_low"],
                mode="lines",
                line=dict(width=0),
                fill="tonexty",
                fillcolor="rgba(239, 68, 68, 0.15)",
                name="Projection range (min/max)",
                hovertemplate=(
                    "%{x|%Y-%m-%d}<br>"
                    "Projected range: $%{y:,.2f}<extra></extra>"
                ),
            )
        )
        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_plot["forecast_date"],
                y=forecast_plot["projected_loss"],
                mode="lines+markers+text",
                text=[
                    f"{int(days)}d: ${value:,.0f}"
                    for days, value in zip(
                        forecast_plot["horizon_days"].tolist(),
                        forecast_plot["projected_loss"].tolist(),
                    )
                ],
                textposition="top center",
                marker=dict(color=COLORS["critical"], size=9),
                line=dict(color=COLORS["critical"], width=3),
                name="Projected cumulative loss",
                hovertemplate="%{x|%Y-%m-%d}<br>Projected cumulative: $%{y:,.2f}<extra></extra>",
            )
        )
        fig_forecast.add_trace(
            go.Scatter(
                x=forecast_plot["forecast_date"],
                y=forecast_plot["baseline_target"],
                mode="lines",
                line=dict(color=COLORS["warning"], width=2, dash="dot"),
                name="Baseline target",
                hovertemplate="%{x|%Y-%m-%d}<br>Baseline target: $%{y:,.2f}<extra></extra>",
            )
        )
        now_line_x = pd.Timestamp(last_date).to_pydatetime()
        fig_forecast.add_shape(
            type="line",
            x0=now_line_x,
            x1=now_line_x,
            y0=0,
            y1=1,
            xref="x",
            yref="paper",
            line=dict(color="#64748b", dash="dash"),
        )
        fig_forecast.add_annotation(
            x=now_line_x,
            y=1,
            xref="x",
            yref="paper",
            text="Now",
            showarrow=False,
            yshift=10,
            font=dict(size=10, color="#64748b"),
        )
        fig_forecast.update_layout(
            template="walmart_fraud",
            margin=dict(t=15, r=8, b=8, l=8),
            xaxis_title="Date",
            yaxis_title="Cumulative Loss (USD)",
            legend_title_text=None,
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

if __name__ == "__main__":
    main()

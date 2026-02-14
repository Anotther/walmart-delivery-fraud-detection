"""
Patterns Page - Advanced fraud pattern detection and behavior intelligence.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import COLORS, kpi_card, load_css, render_sidebar
from src.dashboard.data_cache import get_default_cache

st.set_page_config(
    page_title="Patterns - Walmart Fraud Detection",
    page_icon="W",
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css()

BEHAVIOR_CARD_TOOLTIPS = {
    "temporal_behavior": (
        "Summarizes trend direction and percent change in missing-rate behavior over time. "
        "Delta highlights the highest-risk day and hour."
    ),
    "network_behavior": (
        "Counts recurrent driver-customer pairs that can indicate coordinated or repeated loss behavior."
    ),
    "entity_behavior": (
        "Shows which detector family (driver, customer, collusion, or regional) currently concentrates the "
        "largest number of findings."
    ),
}


@st.cache_data(ttl=720)  # 12-minute TTL for patterns data
def get_patterns_data() -> Tuple[Dict[str, Any], Dict[str, Any], pd.DataFrame, Dict[str, Any], Dict[str, pd.DataFrame]]:
    """
    Fetch patterns data using lazy loading.
    This method uses a 12-minute TTL as pattern detection updates frequently.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for patterns page
    page_data = cache.get_page_data('patterns')

    # Extract required datasets from page data
    patterns = page_data.get('patterns_analysis')
    if patterns is None:
        error_detail = page_data.get('get_patterns_analysis_error')
        if error_detail:
            raise RuntimeError(f"Failed to load patterns analysis: {error_detail}")
        patterns = cache.get_patterns_analysis()

    temporal = page_data.get('advanced_temporal')
    if temporal is None:
        error_detail = page_data.get('get_advanced_temporal_error')
        if error_detail:
            raise RuntimeError(f"Failed to load temporal analysis: {error_detail}")
        temporal = cache.get_advanced_temporal()

    drivers = page_data.get('driver_summary')  # Not in PAGE_CONFIGS but calculated by patterns_analysis

    # Workaround: get_driver_summary is not in PAGE_CONFIGS['patterns']['required_methods']
    # but patterns_analysis might need it. Let's load it separately if needed.
    if drivers is None:
        drivers = cache.get_driver_summary()

    # Product workspace and trends might not be directly in page_data
    # Load them if needed for the page
    workspace = cache.get_product_analysis_workspace()
    trends = cache.get_temporal_trends()

    return patterns, temporal, drivers, workspace, trends


def _query_param(name: str) -> str:
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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _risk_tier(score: float) -> str:
    if score >= 70:
        return "Critical"
    if score >= 40:
        return "High"
    if score > 0:
        return "Medium"
    return "Low"


def _flatten_anomalies(anomaly_details: Dict[str, List[Dict[str, Any]]]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for segment, items in anomaly_details.items():
        for item in items:
            if "period" in item:
                period = str(item["period"])
            elif "day" in item:
                period = str(item["day"])
            elif "hour" in item:
                hour = item.get("hour")
                period = f"{int(hour):02d}:00" if hour is not None else "Unknown"
            else:
                period = "Unknown"

            missing_rate = _to_float(item.get("missing_rate", 0.0), 0.0)
            threshold = _to_float(item.get("threshold", 0.0), 0.0)
            rows.append(
                {
                    "Segment": segment.title(),
                    "Period": period,
                    "Missing Rate (%)": round(missing_rate, 2),
                    "Threshold (%)": round(threshold, 2),
                    "Gap (pp)": round(missing_rate - threshold, 2),
                }
            )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).sort_values(["Gap (pp)", "Missing Rate (%)"], ascending=False)


def build_scope_context(
    workspace: Dict[str, Any],
    fallback_temporal: Dict[str, Any],
    category_filter: str,
    product_filter: str,
) -> Dict[str, Any]:
    """
    Build scoped temporal context for Product -> Patterns drill-down.
    Returns empty dict when no valid scope is available.
    """
    if not category_filter and not product_filter:
        return {}

    missing_items = workspace.get("missing_items", pd.DataFrame()).copy()
    orders = workspace.get("orders", pd.DataFrame()).copy()

    if missing_items.empty or orders.empty:
        return {}

    if category_filter:
        missing_items = missing_items[missing_items["category"].astype(str) == str(category_filter)]
    if product_filter:
        missing_items = missing_items[missing_items["product_id"].astype(str) == str(product_filter)]

    if missing_items.empty:
        return {}

    scope_order_ids = set(missing_items["order_id"].astype(str))
    scoped_orders = orders[orders["order_id"].astype(str).isin(scope_order_ids)].copy()
    if scoped_orders.empty:
        return {}

    scoped_orders["day_of_week"] = scoped_orders["day_of_week"].fillna("Unknown")
    scoped_orders["day_of_week_num"] = pd.to_numeric(
        scoped_orders["day_of_week_num"], errors="coerce"
    ).fillna(99)
    scoped_orders["delivery_hour"] = pd.to_numeric(
        scoped_orders["delivery_hour"], errors="coerce"
    ).fillna(0).astype(int)

    daily = (
        scoped_orders.groupby(["day_of_week", "day_of_week_num"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            items_delivered=("items_delivered", "sum"),
            items_missing=("items_missing", "sum"),
        )
        .sort_values("day_of_week_num")
    )
    daily["missing_rate"] = np.where(
        (daily["items_delivered"] + daily["items_missing"]) > 0,
        (daily["items_missing"] / (daily["items_delivered"] + daily["items_missing"])) * 100,
        0.0,
    )

    hourly = (
        scoped_orders.groupby("delivery_hour", as_index=False)
        .agg(
            orders=("order_id", "count"),
            items_delivered=("items_delivered", "sum"),
            items_missing=("items_missing", "sum"),
        )
        .rename(columns={"delivery_hour": "hour"})
        .sort_values("hour")
    )
    hourly["missing_rate"] = np.where(
        (hourly["items_delivered"] + hourly["items_missing"]) > 0,
        (hourly["items_missing"] / (hourly["items_delivered"] + hourly["items_missing"])) * 100,
        0.0,
    )

    monthly = (
        scoped_orders.groupby(["month", "month_name"], as_index=False)
        .agg(
            orders=("order_id", "count"),
            items_delivered=("items_delivered", "sum"),
            items_missing=("items_missing", "sum"),
        )
        .sort_values("month")
    )
    monthly["missing_rate"] = np.where(
        (monthly["items_delivered"] + monthly["items_missing"]) > 0,
        (monthly["items_missing"] / (monthly["items_delivered"] + monthly["items_missing"])) * 100,
        0.0,
    )

    def _threshold_anomalies(df: pd.DataFrame, period_col: str, metric_col: str, label: str) -> List[Dict[str, Any]]:
        if df.empty:
            return []
        avg = float(df[metric_col].mean())
        std = float(df[metric_col].std())
        threshold = avg + (2 * std if std > 0 else 0)
        alerts: List[Dict[str, Any]] = []
        for _, row in df[df[metric_col] > threshold].iterrows():
            payload: Dict[str, Any] = {
                "missing_rate": float(row[metric_col]),
                "threshold": threshold,
            }
            payload[label] = row[period_col]
            alerts.append(payload)
        return alerts

    anomalies = {
        "daily": _threshold_anomalies(daily, "day_of_week", "missing_rate", "day"),
        "hourly": _threshold_anomalies(hourly, "hour", "missing_rate", "hour"),
        "monthly": _threshold_anomalies(monthly, "month_name", "missing_rate", "period"),
    }

    if len(monthly) >= 2:
        first_ref = float(monthly.head(max(1, len(monthly) // 2))["missing_rate"].mean())
        last_ref = float(monthly.tail(max(1, len(monthly) // 2))["missing_rate"].mean())
        change_pct = _safe_ratio(last_ref - first_ref, first_ref) * 100 if first_ref > 0 else 0.0
        direction = "increasing" if change_pct > 0.5 else "decreasing" if change_pct < -0.5 else "stable"
    else:
        change_pct = float(fallback_temporal.get("trend", {}).get("change_pct", 0.0))
        direction = str(fallback_temporal.get("trend", {}).get("direction", "stable"))

    worst_day = (
        str(daily.loc[daily["missing_rate"].idxmax(), "day_of_week"])
        if not daily.empty
        else str(fallback_temporal.get("patterns", {}).get("worst_day", "Unknown"))
    )
    worst_hour = (
        int(hourly.loc[hourly["missing_rate"].idxmax(), "hour"])
        if not hourly.empty
        else fallback_temporal.get("patterns", {}).get("worst_hour")
    )

    scope_driver_ids = set(scoped_orders["driver_id"].astype(str))
    scope_customer_ids = set(scoped_orders["customer_id"].astype(str))
    scope_regions = set(scoped_orders["region"].astype(str))
    scope_pairs = set(
        (scoped_orders["driver_id"].astype(str) + "_" + scoped_orders["customer_id"].astype(str)).tolist()
    )

    return {
        "daily": daily,
        "hourly": hourly,
        "monthly": monthly,
        "anomalies": {
            "total": int(sum(len(v) for v in anomalies.values())),
            "details": anomalies,
        },
        "trend": {
            "direction": direction,
            "change_pct": float(change_pct),
        },
        "patterns": {
            "worst_day": worst_day,
            "worst_hour": worst_hour,
        },
        "scope_meta": {
            "orders": int(len(scoped_orders)),
            "missing_items": int(len(missing_items)),
            "category": category_filter or "All",
            "product_id": product_filter or "All",
        },
        "scope_ids": {
            "drivers": scope_driver_ids,
            "customers": scope_customer_ids,
            "regions": scope_regions,
            "pairs": scope_pairs,
        },
    }


def _build_behavior_snapshot(active_temporal: Dict[str, Any], active_patterns: Dict[str, List[Any]]) -> Dict[str, Any]:
    trend = active_temporal.get("trend", {})
    anomalies = active_temporal.get("anomalies", {})
    pattern_stats = active_temporal.get("patterns", {})

    trend_direction = str(trend.get("direction", "stable")).lower()
    change_pct = _to_float(trend.get("change_pct", 0.0), 0.0)
    anomaly_total = int(anomalies.get("total", 0) or 0)

    worst_day = str(pattern_stats.get("worst_day", "Unknown"))
    worst_hour = pattern_stats.get("worst_hour")
    if worst_hour is None:
        hourly_df = active_temporal.get("hourly", pd.DataFrame())
        if isinstance(hourly_df, pd.DataFrame) and not hourly_df.empty and {"hour", "missing_rate"}.issubset(hourly_df.columns):
            worst_hour = int(hourly_df.loc[hourly_df["missing_rate"].idxmax(), "hour"])

    pattern_counts = {
        "driver_patterns": len(active_patterns.get("driver_patterns", [])),
        "customer_patterns": len(active_patterns.get("customer_patterns", [])),
        "collusion_patterns": len(active_patterns.get("collusion_patterns", [])),
        "regional_patterns": len(active_patterns.get("regional_patterns", [])),
    }
    total_findings = int(sum(pattern_counts.values()))
    collusion_count = int(pattern_counts["collusion_patterns"])

    dominant_key = max(pattern_counts, key=pattern_counts.get)
    dominant_value = pattern_counts[dominant_key]
    dominant_map = {
        "driver_patterns": "Driver-linked signals dominate",
        "customer_patterns": "Customer-linked signals dominate",
        "collusion_patterns": "Network collusion signals dominate",
        "regional_patterns": "Regional hotspot signals dominate",
    }
    dominant_label = dominant_map.get(dominant_key, "No dominant entity signal") if dominant_value > 0 else "No dominant entity signal"

    if trend_direction in {"increasing", "decreasing", "stable"}:
        temporal_value = f"{trend_direction.title()} ({change_pct:+.1f}%)"
    else:
        temporal_value = "Insufficient signal"

    temporal_context = f"Peak risk day: {worst_day}"
    if worst_hour is not None:
        temporal_context = f"{temporal_context} | Peak hour: {int(worst_hour):02d}:00"

    snapshot = {
        "insufficient": not bool(active_temporal),
        "trend_direction": trend_direction,
        "change_pct": change_pct,
        "anomaly_total": anomaly_total,
        "total_findings": total_findings,
        "collusion_count": collusion_count,
        "temporal_value": temporal_value,
        "temporal_context": temporal_context,
        "network_value": f"{collusion_count} recurrent pairs",
        "network_context": "Repeated driver-customer links can indicate coordinated loss behavior.",
        "entity_value": dominant_label,
        "entity_context": f"{total_findings} detector findings mapped across entities.",
    }
    return snapshot


def _build_behavior_takeaway(snapshot: Dict[str, Any]) -> str:
    if snapshot.get("insufficient", False):
        return "Insufficient data to infer behavior pattern."

    direction = snapshot.get("trend_direction", "stable")
    anomaly_total = int(snapshot.get("anomaly_total", 0))
    total_findings = int(snapshot.get("total_findings", 0))
    collusion_count = int(snapshot.get("collusion_count", 0))

    if direction == "increasing" and anomaly_total > 0:
        return (
            "Fraud behavior is accelerating: temporal anomalies are above baseline and the trend is moving upward. "
            "Prioritize short-cycle interventions on peak windows."
        )
    if direction == "decreasing":
        return (
            "Fraud pressure is cooling versus the earlier period. Keep continuous monitoring to avoid rebound effects "
            "and maintain controls on recurrent entities."
        )
    if direction == "stable" and anomaly_total <= 1 and total_findings <= 3:
        return (
            "Fraud behavior is currently stable with localized signals. Maintain baseline controls and watch for "
            "network recurrence."
        )
    if collusion_count > 0:
        return (
            "Trend is mixed, but recurrent driver-customer links remain active. Operational focus should prioritize "
            "network-based investigations."
        )
    return (
        "Fraud behavior remains mixed across temporal and entity dimensions. Continue targeted monitoring and "
        "weekly calibration of detector thresholds."
    )


def _render_header() -> None:
    st.markdown("### Operational Intelligence")
    st.markdown(
        """
        <div class="dashboard-header-row">
            <div>
                <h1 style="margin:0; font-size: 2.5rem;">Patterns Intelligence Hub</h1>
                <p class="text-muted">Behavioral signals that explain when fraud concentrates, who drives exposure, and where recurrence emerges.</p>
            </div>
            <div class="scope-badge-container">
                 <span class="badge badge-success">Pattern Scope</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")


def _render_behavior_section(snapshot: Dict[str, Any]) -> None:
    st.markdown("### How Fraud Behaves")

    direction = snapshot.get("trend_direction", "stable")
    temporal_color = COLORS["critical"] if direction == "increasing" else COLORS["success"] if direction == "decreasing" else COLORS["warning"]
    network_color = COLORS["critical"] if snapshot.get("collusion_count", 0) > 0 else COLORS["success"]
    entity_color = COLORS["warning"] if snapshot.get("total_findings", 0) > 0 else COLORS["success"]

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card(
            "Temporal Behavior",
            str(snapshot.get("temporal_value", "Insufficient signal")),
            delta=str(snapshot.get("temporal_context", "Insufficient data")),
            delta_color="neutral",
            color=temporal_color,
            tooltip=BEHAVIOR_CARD_TOOLTIPS["temporal_behavior"],
        )
    with c2:
        kpi_card(
            "Network Behavior",
            str(snapshot.get("network_value", "0 recurrent pairs")),
            delta=str(snapshot.get("network_context", "Insufficient data")),
            delta_color="neutral",
            color=network_color,
            tooltip=BEHAVIOR_CARD_TOOLTIPS["network_behavior"],
        )
    with c3:
        kpi_card(
            "Entity Behavior",
            str(snapshot.get("entity_value", "No dominant entity signal")),
            delta=str(snapshot.get("entity_context", "No findings available")),
            delta_color="neutral",
            color=entity_color,
            tooltip=BEHAVIOR_CARD_TOOLTIPS["entity_behavior"],
        )

    st.markdown("<div style='height: 0.35rem;'></div>", unsafe_allow_html=True)
    st.info(f"Executive Takeaway: {_build_behavior_takeaway(snapshot)}")


def _render_temporal_section(active_temporal: Dict[str, Any], trends: Dict[str, pd.DataFrame], scope_context: Dict[str, Any]) -> None:
    st.markdown("### Temporal Signals")

    trend = active_temporal.get("trend", {})
    temp_anomalies = active_temporal.get("anomalies", {"total": 0, "details": {}})
    pattern_stats = active_temporal.get("patterns", {})

    trend_direction = str(trend.get("direction", "stable")).title()
    trend_change = _to_float(trend.get("change_pct", 0.0), 0.0)
    anomaly_total = int(temp_anomalies.get("total", 0) or 0)
    worst_day = str(pattern_stats.get("worst_day", "Unknown"))
    worst_hour = pattern_stats.get("worst_hour")
    peak_window = f"{worst_day}"
    if worst_hour is not None:
        peak_window = f"{peak_window} @ {int(worst_hour):02d}:00"

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        trend_color = COLORS["critical"] if trend_direction == "Increasing" else COLORS["success"] if trend_direction == "Decreasing" else COLORS["warning"]
        kpi_card("Fraud Trend", trend_direction, delta="Direction from temporal slope", delta_color="neutral", color=trend_color)
    with k2:
        kpi_card(
            "Trend Change",
            f"{trend_change:+.2f}%",
            delta="First vs last period missing rate",
            delta_color="neutral",
            color=COLORS["warning"] if trend_change > 0 else COLORS["success"],
        )
    with k3:
        kpi_card(
            "Temporal Anomalies",
            f"{anomaly_total}",
            delta="Outliers above mean + 2 SD threshold",
            delta_color="neutral",
            color=COLORS["critical"] if anomaly_total > 0 else COLORS["success"],
        )
    with k4:
        kpi_card(
            "Peak Risk Window",
            peak_window,
            delta="Highest missing-rate concentration",
            delta_color="neutral",
            color=COLORS["walmart_yellow"],
        )

    st.markdown("<div style='height: 1.1rem;'></div>", unsafe_allow_html=True)
    st.markdown("#### Missing Rate by Day of Week")
    daily_df = scope_context.get("daily") if scope_context else trends.get("daily", pd.DataFrame())

    if daily_df is None or daily_df.empty or "missing_rate" not in daily_df.columns or "day_of_week" not in daily_df.columns:
        st.warning("Insufficient data for temporal day-of-week visualization.")
    else:
        plot_df = daily_df.copy()
        day_order_col = "day_of_week_num" if "day_of_week_num" in plot_df.columns else "day_num" if "day_num" in plot_df.columns else None
        if day_order_col:
            plot_df = plot_df.sort_values(day_order_col)

        plot_df["missing_rate"] = pd.to_numeric(plot_df["missing_rate"], errors="coerce").fillna(0.0)
        baseline = float(plot_df["missing_rate"].mean())
        plot_df["signal_band"] = np.where(
            plot_df["missing_rate"] >= baseline,
            "Above Baseline",
            "Below Baseline",
        )
        plot_df["rate_label"] = plot_df["missing_rate"].map(lambda value: f"{value:.2f}%")

        order_col = "orders" if "orders" in plot_df.columns else "total_orders" if "total_orders" in plot_df.columns else None
        if order_col:
            plot_df[order_col] = pd.to_numeric(plot_df[order_col], errors="coerce").fillna(0).astype(int)
            customdata = plot_df[["rate_label", order_col]].to_numpy()
            hovertemplate = (
                "Day: %{x}<br>"
                "Missing Rate: %{customdata[0]}<br>"
                "Orders: %{customdata[1]}"
                "<extra></extra>"
            )
        else:
            customdata = plot_df[["rate_label"]].to_numpy()
            hovertemplate = (
                "Day: %{x}<br>"
                "Missing Rate: %{customdata[0]}"
                "<extra></extra>"
            )

        fig = px.bar(
            plot_df,
            x="day_of_week",
            y="missing_rate",
            color="signal_band",
            color_discrete_map={
                "Above Baseline": COLORS["critical"],
                "Below Baseline": COLORS["walmart_blue_light"],
            },
            text="rate_label",
        )
        fig.add_hline(
            y=baseline,
            line_dash="dash",
            line_color=COLORS["warning"],
            annotation_text=f"Baseline {baseline:.2f}%",
            annotation_position="top right",
        )
        fig.update_layout(
            xaxis_title="Day of Week",
            yaxis_title="Missing Rate (%)",
            legend_title_text="Band",
            margin=dict(t=20, l=10, r=10, b=30),
            plot_bgcolor=COLORS['plot_bg'],
            paper_bgcolor=COLORS['paper_bg'],
            font_family=COLORS['font_family'],
        )
        fig.update_traces(textposition="outside", customdata=customdata, hovertemplate=hovertemplate)
        st.plotly_chart(fig, use_container_width=True)


def _render_network_section(active_patterns: Dict[str, List[Any]], drivers_df: pd.DataFrame) -> None:
    st.markdown("### Network Behavior")

    tab_net, tab_corr = st.tabs(["Collusion Detection", "Feature Correlations"])

    with tab_net:
        collusion = active_patterns.get("collusion_patterns", [])
        st.caption(f"Potential collusion pairs detected: {len(collusion)}")

        if collusion:
            collusion_rows = []
            for indicator in collusion:
                missing_rate = _to_float(indicator.details.get("missing_rate", 0.0), 0.0)
                score = _to_float(indicator.score, 0.0)
                collusion_rows.append(
                    {
                        "Driver": indicator.details.get("driver_id", "-"),
                        "Customer": indicator.details.get("customer_id", "-"),
                        "Interactions": int(indicator.details.get("interactions", 0) or 0),
                        "Missing Items": int(indicator.details.get("items_missing", 0) or 0),
                        "Missing Rate (%)": round(missing_rate, 2),
                        "Score": round(score, 1),
                        "Risk Tier": _risk_tier(score),
                    }
                )
            collusion_df = pd.DataFrame(collusion_rows).sort_values("Score", ascending=False)
            st.dataframe(collusion_df, use_container_width=True, hide_index=True)
            st.caption("Recurrent pairs with high missing-rate concentration are prioritized for investigation.")
        else:
            st.info("No collusion patterns detected matching configured thresholds.")

    with tab_corr:
        st.markdown("#### Driver Feature Correlation Matrix")
        if drivers_df.empty:
            st.warning("Insufficient data for correlation analysis.")
            return

        corr_cols = [
            "total_orders",
            "total_items_delivered",
            "total_items_missing",
            "missing_rate",
            "avg_order_value",
            "risk_score",
        ]
        corr_cols = [column for column in corr_cols if column in drivers_df.columns]

        if len(corr_cols) < 2:
            st.warning("Not enough numeric columns are available to compute a robust correlation matrix.")
            return

        corr_df = drivers_df[corr_cols].apply(pd.to_numeric, errors="coerce")
        corr = corr_df.corr()

        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            aspect="auto",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
            labels={"color": "Correlation"},
        )
        fig_corr.update_layout(
            title_text="Correlation Matrix: Driver Risk Signals",
            margin=dict(t=45, l=10, r=10, b=10),
            font_family=COLORS['font_family'],
        )
        st.plotly_chart(fig_corr, use_container_width=True)
        st.caption("Stronger positive values indicate variables moving together with missing-item risk.")


def _render_detector_section(active_patterns: Dict[str, List[Any]]) -> None:
    st.markdown("### Detector Output")

    detectors = [
        {
            "name": "Driver Pattern Anomalies",
            "count": len(active_patterns.get("driver_patterns", [])),
            "desc": "Deviation from peer benchmark behavior",
            "color": COLORS["warning"],
        },
        {
            "name": "Customer Claim Frequency",
            "count": len(active_patterns.get("customer_patterns", [])),
            "desc": "Abnormal claim velocity versus spend",
            "color": COLORS["warning"],
        },
        {
            "name": "Network Collusion",
            "count": len(active_patterns.get("collusion_patterns", [])),
            "desc": "Recurrent loss pairings in driver-customer links",
            "color": COLORS["critical"],
        },
        {
            "name": "Regional Hotspots",
            "count": len(active_patterns.get("regional_patterns", [])),
            "desc": "Geospatial concentration of high-risk behavior",
            "color": COLORS["walmart_blue_light"],
        },
    ]

    d1, d2, d3, d4 = st.columns(4)
    for detector, column in zip(detectors, [d1, d2, d3, d4]):
        with column:
            active_color = detector["color"] if detector["count"] > 0 else COLORS["success"]
            kpi_card(
                detector["name"],
                f"{detector['count']}",
                delta=detector["desc"],
                delta_color="neutral",
                color=active_color,
            )

    st.markdown("#### Latest Findings Log")
    all_findings: List[Dict[str, Any]] = []
    for pattern_type, items in active_patterns.items():
        for item in items:
            score = _to_float(item.score, 0.0)
            all_findings.append(
                {
                    "Algorithm": pattern_type.replace("_patterns", "").replace("_", " ").title(),
                    "Entity": str(item.entity_id),
                    "Score": round(score, 1),
                    "Risk Tier": _risk_tier(score),
                    "Indicator": str(item.indicator_name),
                }
            )

    if all_findings:
        findings_df = pd.DataFrame(all_findings).sort_values("Score", ascending=False).head(10)
        st.dataframe(findings_df, use_container_width=True, hide_index=True)
    else:
        st.success("Clean log. No active detector findings.")


def main() -> None:
    render_sidebar()
    _render_header()

    try:
        scope_category = _query_param("product_category")
        scope_product = _query_param("product_id")
        scope_source = _query_param("source_page")

        with st.spinner("Running pattern recognition algorithms..."):
            patterns, temporal, drivers_df, workspace, trends = get_patterns_data()

        scope_context = build_scope_context(
            workspace=workspace,
            fallback_temporal=temporal,
            category_filter=scope_category,
            product_filter=scope_product,
        )

        active_temporal = scope_context if scope_context else temporal
        active_patterns = patterns

        if scope_context:
            ids = scope_context.get("scope_ids", {})
            driver_ids = ids.get("drivers", set())
            customer_ids = ids.get("customers", set())
            region_ids = ids.get("regions", set())
            pair_ids = ids.get("pairs", set())

            active_patterns = {
                "driver_patterns": [
                    pattern
                    for pattern in patterns.get("driver_patterns", [])
                    if str(getattr(pattern, "entity_id", "")) in driver_ids
                ],
                "customer_patterns": [
                    pattern
                    for pattern in patterns.get("customer_patterns", [])
                    if str(getattr(pattern, "entity_id", "")) in customer_ids
                ],
                "collusion_patterns": [
                    pattern
                    for pattern in patterns.get("collusion_patterns", [])
                    if f"{pattern.details.get('driver_id')}_{pattern.details.get('customer_id')}" in pair_ids
                ],
                "regional_patterns": [
                    pattern
                    for pattern in patterns.get("regional_patterns", [])
                    if str(getattr(pattern, "entity_id", "")) in region_ids
                ],
            }

            if not drivers_df.empty and "driver_id" in drivers_df.columns:
                drivers_df = drivers_df[drivers_df["driver_id"].astype(str).isin(driver_ids)]

            scope_meta = scope_context.get("scope_meta", {})
            st.info(
                "Scoped pattern analysis active: "
                f"category={scope_meta.get('category', 'All')} | "
                f"product_id={scope_meta.get('product_id', 'All')} | "
                f"orders={scope_meta.get('orders', 0)} | "
                f"missing_items={scope_meta.get('missing_items', 0)} "
                f"(source: {scope_source or 'product_analysis'})"
            )

        behavior_snapshot = _build_behavior_snapshot(active_temporal, active_patterns)
        _render_behavior_section(behavior_snapshot)

        st.markdown("---")
        _render_temporal_section(active_temporal, trends, scope_context)

        st.markdown("---")
        _render_network_section(active_patterns, drivers_df)

        st.markdown("---")
        _render_detector_section(active_patterns)

    except Exception as exc:
        st.error(f"Error loading patterns: {exc}")


if __name__ == "__main__":
    main()

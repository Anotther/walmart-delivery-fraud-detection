"""
Patterns Page - Advanced fraud pattern detection and algorithms.
"""
import streamlit as st
import sys
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import load_css, kpi_card, COLORS, render_sidebar, risk_badge
from src.dashboard.data_cache import get_default_cache

st.set_page_config(page_title="Patterns - Walmart Fraud Detection", page_icon="🧬", layout="wide")
load_css()
render_sidebar()

st.title("Advanced Patterns & Algorithms")
st.markdown("Deep dive into temporal anomalies, network effects, and algorithmic detection.")

@st.cache_data(ttl=900)
def get_patterns_data():
    cache = get_default_cache()
    # Fetch data parallelly in real scenario, sequential here
    patterns = cache.get_patterns_analysis()
    temporal = cache.get_advanced_temporal()
    
    # We also need feature data for correlation
    # We can get this from driver/customer summaries
    drivers = cache.get_driver_summary()
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

    def _threshold_anomalies(df: pd.DataFrame, period_col: str, metric_col: str, label: str):
        if df.empty:
            return []
        avg = float(df[metric_col].mean())
        std = float(df[metric_col].std())
        threshold = avg + (2 * std if std > 0 else 0)
        alerts = []
        for _, row in df[df[metric_col] > threshold].iterrows():
            payload = {
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
                p for p in patterns.get("driver_patterns", [])
                if str(getattr(p, "entity_id", "")) in driver_ids
            ],
            "customer_patterns": [
                p for p in patterns.get("customer_patterns", [])
                if str(getattr(p, "entity_id", "")) in customer_ids
            ],
            "collusion_patterns": [
                p
                for p in patterns.get("collusion_patterns", [])
                if f"{p.details.get('driver_id')}_{p.details.get('customer_id')}" in pair_ids
            ],
            "regional_patterns": [
                p for p in patterns.get("regional_patterns", [])
                if str(getattr(p, "entity_id", "")) in region_ids
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

    # 1. Temporal Patterns
    # --------------------
    st.header("1. Temporal Patterns")
    
    # Metrics
    temp_anomalies = active_temporal['anomalies']
    trend = active_temporal['trend']
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    with col_t1:
        direction_icon = "📈" if trend['direction'] == 'increasing' else "📉"
        kpi_card("Fraud Trend", f"{trend['direction'].title()} {direction_icon}", color=COLORS['walmart_blue'])
    with col_t2:
        kpi_card("Trend Change", f"{trend['change_pct']:.1f}%", color=COLORS['warning'] if trend['change_pct'] > 0 else COLORS['success'])
    with col_t3:
        kpi_card("Temporal Anomalies", f"{temp_anomalies['total']}", color=COLORS['critical'])
    with col_t4:
        kpi_card("Peak Risk Period", f"{active_temporal['patterns']['worst_day']}s", color=COLORS['walmart_yellow'])

    # Heatmap & Anomalies
    col_tm, col_ts = st.columns([2, 1])
    
    with col_tm:
        st.subheader("Risk Heatmap: Hour vs Day")
        daily = scope_context.get('daily') if scope_context else trends['daily']

        fig = px.bar(
            daily, 
            x="day_of_week", 
            y="missing_rate", 
            color="missing_rate",
            title="Missing Rate by Day of Week",
            color_continuous_scale="Reds"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_ts:
        st.subheader("Detected Anomalies")
        if temp_anomalies['total'] > 0:
            for category, items in temp_anomalies['details'].items():
                if items:
                    st.markdown(f"**{category.title()}**")
                    for item in items:
                        if 'period' in item: p = item['period']
                        elif 'day' in item: p = item['day']
                        elif 'hour' in item: p = f"{item['hour']}:00"
                        else: p = 'Unknown'
                        
                        st.error(f"{p}: Rate {item['missing_rate']:.1f}% (Threshold: {item['threshold']:.1f}%)")
        else:
            st.success("No significant temporal anomalies detected.")

    st.divider()

    # 2. Network & Correlations
    # -------------------------
    st.header("2. Network & Correlations")
    
    tab_net, tab_corr = st.tabs(["Collusion Detection", "Feature Correlations"])
    
    with tab_net:
        collusion = active_patterns.get('collusion_patterns', [])
        st.markdown(f"**Potential Collusion Pairs Detected**: {len(collusion)}")
        
        if collusion:
            collusion_data = []
            for p in collusion:
                collusion_data.append({
                    "Driver": p.details['driver_id'],
                    "Customer": p.details['customer_id'],
                    "Interactions": p.details['interactions'],
                    "Missing Items": p.details['items_missing'],
                    "Missing Rate": f"{p.details['missing_rate']:.1f}%",
                    "Score": p.score
                })
            st.dataframe(pd.DataFrame(collusion_data).sort_values("Score", ascending=False), use_container_width=True)
        else:
            st.info("No collusion patterns detected matching thresholds.")
            
    with tab_corr:
        st.subheader("Driver Feature Correlation")
        # Select numeric columns for correlation
        if not drivers_df.empty:
            corr_cols = ['total_orders', 'total_items_delivered', 'total_items_missing', 
                         'missing_rate', 'avg_order_value', 'risk_score']
            # Filter only existing columns
            corr_cols = [c for c in corr_cols if c in drivers_df.columns]
            
            corr = drivers_df[corr_cols].corr()
            fig_corr = px.imshow(
                corr, 
                text_auto=True,
                aspect="auto",
                color_continuous_scale="RdBu_r",
                title="Correlation Matrix: Driver Risk Factors"
            )
            st.plotly_chart(fig_corr, use_container_width=True)
        else:
            st.warning("Insufficient data for correlation analysis.")

    st.divider()

    # 3. Algorithms Summary
    # ---------------------
    st.header("3. Algorithmic Detectors")
    
    detectors = [
        {"name": "Driver Pattern Anomalies", "count": len(active_patterns.get('driver_patterns', [])), "desc": "Deviation from peer benchmarks (Mean + 2SD)"},
        {"name": "Customer Claim Frequency", "count": len(active_patterns.get('customer_patterns', [])), "desc": "Abnormal claim velocity vs spend"},
        {"name": "Network Collusion", "count": len(active_patterns.get('collusion_patterns', [])), "desc": "Driver-Customer recurrent loss pairings"},
        {"name": "Regional Hotspots", "count": len(active_patterns.get('regional_patterns', [])), "desc": "Geospatial high-risk zones"},
    ]
    
    col_alg1, col_alg2 = st.columns([1, 1])
    
    with col_alg1:
        st.markdown("### Active Detectors Status")
        for d in detectors:
            status_color = "red" if d['count'] > 0 else "green"
            st.markdown(f"""
            <div style="padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-bottom: 10px; border-left: 5px solid {status_color}">
                <strong>{d['name']}</strong><br>
                <span style="font-size: 0.9em; color: #666;">{d['desc']}</span>
                <div style="float: right; font-weight: bold;">{d['count']} Findings</div>
            </div>
            """, unsafe_allow_html=True)
            
    with col_alg2:
         st.markdown("### Latest Findings Log")
         # Flatten all patterns
         all_findings = []
         for p_type, items in active_patterns.items():
            for item in items:
                all_findings.append({
                    "Algorithm": p_type.replace('_patterns', '').title(),
                    "Entity": item.entity_id,
                    "Score": item.score,
                    "Indicator": item.indicator_name
                })
         
         if all_findings:
             df_log = pd.DataFrame(all_findings).sort_values("Score", ascending=False).head(10)
             st.dataframe(df_log, use_container_width=True, hide_index=True)
         else:
             st.success("Clean log. No active findings.")

except Exception as e:
    st.error(f"Error loading patterns: {e}")

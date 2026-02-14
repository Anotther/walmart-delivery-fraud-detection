"""
Drivers Page - Driver monitoring & performance analysis.
"""
import streamlit as st
import streamlit.components.v1 as components
import sys
import inspect
from pathlib import Path
from datetime import date
from html import escape

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.dashboard.components import (
    load_css,
    kpi_card,
    insight_card,
    plot_correlation_heatmap,
    plot_hypothesis_card,
    risk_badge,
    render_sidebar,
    COLORS
)
from src.dashboard.data_cache import get_default_cache
from src.database.connection import load_drivers
from src.features.driver_features import (
    create_driver_features,
    get_driver_risk_scores,
    compare_driver_performance
)
from src.analysis.temporal import detect_temporal_anomalies

st.set_page_config(page_title="Drivers - Walmart Fraud Detection", page_icon="🚚", layout="wide")
load_css()

ITEM_VALUE_USD = 15


@st.cache_data(ttl=900)  # 15-minute TTL for driver data
def load_base_data():
    """
    Load base data for drivers page using lazy loading where possible.
    This method uses a 15-minute TTL as driver performance is stable.
    """
    cache = get_default_cache()

    # Use lazy loading - only loads data needed for drivers page
    page_data = cache.get_page_data('drivers')

    # Extract driver summary from page data
    drivers_summary = page_data['driver_summary']

    # Load additional data needed for the page
    orders = cache.get_orders_with_features()
    drivers = load_drivers()

    return orders, drivers, drivers_summary


@st.cache_data(ttl=600)
def build_driver_snapshot(orders: pd.DataFrame, drivers: pd.DataFrame) -> pd.DataFrame:
    driver_features = create_driver_features(drivers, orders)
    driver_risk = get_driver_risk_scores(driver_features)

    # Primary region per driver (mode)
    if "region" in orders.columns:
        primary_region = orders.groupby("driver_id")["region"].agg(
            lambda x: x.value_counts().index[0] if len(x) else None
        )
        driver_risk["primary_region"] = driver_risk["driver_id"].map(primary_region)
    else:
        driver_risk["primary_region"] = None

    # Monetary impact proxy
    driver_risk["missing_value"] = driver_risk["total_items_missing"] * ITEM_VALUE_USD
    return driver_risk[driver_risk["total_orders"] > 0]


@st.cache_data(ttl=600)
def build_driver_monthly(orders: pd.DataFrame) -> pd.DataFrame:
    monthly = orders.groupby(["driver_id", "month", "month_name"]).agg({
        "order_id": "count",
        "items_delivered": "sum",
        "items_missing": "sum",
        "order_amount": "sum",
    }).reset_index()

    monthly.columns = [
        "driver_id", "month", "month_name", "orders",
        "items_delivered", "items_missing", "revenue"
    ]
    monthly["total_items"] = monthly["items_delivered"] + monthly["items_missing"]
    monthly["missing_rate"] = np.where(
        monthly["total_items"] > 0,
        (monthly["items_missing"] / monthly["total_items"]) * 100,
        0
    )
    return monthly.sort_values(["driver_id", "month"])


@st.cache_data(ttl=600)
def compute_hypotheses(orders: pd.DataFrame, drivers: pd.DataFrame, driver_df: pd.DataFrame) -> list:
    results = []

    # H1: Driver experience vs missing rate
    valid = driver_df[(driver_df["trips"].notna()) & (driver_df["total_orders"] > 0)]
    if len(valid) >= 3 and valid["trips"].nunique() > 1:
        corr, p_value = stats.pearsonr(valid["trips"], valid["missing_rate"])
    else:
        corr, p_value = 0.0, 1.0

    exp_bins = pd.cut(valid["trips"], bins=[-1, 25, 50, 100, float("inf")],
                      labels=["Novice", "Intermediate", "Experienced", "Expert"])
    exp_rates = valid.groupby(exp_bins)["missing_rate"].mean().dropna()
    novice_rate = float(exp_rates.get("Novice", np.nan))
    expert_rate = float(exp_rates.get("Expert", np.nan))

    results.append({
        "id": "H1",
        "statement": "Driver experience correlates with missing rate",
        "methodology": "Pearson Correlation",
        "metric_name": "Correlation (r)",
        "metric_value": corr,
        "p_value": p_value,
        "status": "Validated" if p_value < 0.05 else "Investigating",
        "result_text": (
            f"Correlation r={corr:.2f}. Missing rate: Novice {novice_rate:.2f}% vs Expert {expert_rate:.2f}%"
            if np.isfinite(novice_rate) and np.isfinite(expert_rate)
            else f"Correlation r={corr:.2f}"
        ),
        "visual_data": valid[["total_orders", "missing_rate"]].to_dict("records")
    })

    # H2: Geographic concentration
    regional = orders.groupby("region").agg({
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_id": "count"
    }).reset_index()
    regional["total_items"] = regional["items_delivered"] + regional["items_missing"]
    regional["missing_rate"] = np.where(
        regional["total_items"] > 0,
        (regional["items_missing"] / regional["total_items"]) * 100,
        0
    )
    avg_rate = regional["missing_rate"].mean()
    std_rate = regional["missing_rate"].std()
    threshold = avg_rate + 2 * std_rate
    hotspots = regional[regional["missing_rate"] > threshold]

    results.append({
        "id": "H2",
        "statement": "Regional concentration indicates collusion risk",
        "methodology": "Threshold + Variance Analysis",
        "metric_name": "Hotspot Count",
        "metric_value": len(hotspots),
        "p_value": None,
        "status": "Validated" if len(hotspots) > 0 else "Rejected",
        "result_text": (
            f"{len(hotspots)} regions above threshold ({threshold:.2f}%)."
        ),
        "visual_data": regional[["region", "missing_rate"]].to_dict("records")
    })

    # H3: Temporal patterns
    orders = orders.copy()
    orders["order_missing_rate"] = np.where(
        orders["total_items"] > 0,
        (orders["items_missing"] / orders["total_items"]) * 100,
        0
    )
    orders["period"] = pd.cut(
        orders["delivery_hour"],
        bins=[-1, 6, 12, 18, 24],
        labels=["Night", "Morning", "Afternoon", "Evening"]
    )
    night = orders[orders["period"] == "Night"]["order_missing_rate"]
    rest = orders[orders["period"] != "Night"]["order_missing_rate"]

    if len(night) > 2 and len(rest) > 2:
        t_stat, p_value = stats.ttest_ind(night, rest, equal_var=False, nan_policy="omit")
    else:
        t_stat, p_value = 0.0, 1.0

    night_rate = night.mean() if len(night) else np.nan
    rest_rate = rest.mean() if len(rest) else np.nan

    results.append({
        "id": "H3",
        "statement": "Night deliveries show higher missing rates",
        "methodology": "Two-sample T-test",
        "metric_name": "Mean Gap",
        "metric_value": (night_rate - rest_rate) if np.isfinite(night_rate) and np.isfinite(rest_rate) else 0.0,
        "p_value": p_value,
        "status": "Validated" if p_value < 0.05 else "Investigating",
        "result_text": (
            f"Night {night_rate:.2f}% vs Rest {rest_rate:.2f}%"
            if np.isfinite(night_rate) and np.isfinite(rest_rate)
            else "Insufficient data"
        ),
        "visual_data": None
    })

    # H4: High-value orders have different risk profiles
    high_value_threshold = orders["order_amount"].quantile(0.75)
    high_value = orders[orders["order_amount"] >= high_value_threshold]["order_missing_rate"]
    low_value = orders[orders["order_amount"] < high_value_threshold]["order_missing_rate"]

    if len(high_value) > 2 and len(low_value) > 2:
        u_stat, p_value = stats.mannwhitneyu(high_value, low_value, alternative="two-sided")
    else:
        u_stat, p_value = 0.0, 1.0

    results.append({
        "id": "H4",
        "statement": "High-value orders have higher missing rates",
        "methodology": "Mann-Whitney U",
        "metric_name": "Median Gap",
        "metric_value": (high_value.median() - low_value.median()) if len(high_value) and len(low_value) else 0.0,
        "p_value": p_value,
        "status": "Validated" if p_value < 0.05 else "Rejected",
        "result_text": (
            f"Median gap {high_value.median():.2f}pp (high vs low)."
            if len(high_value) and len(low_value)
            else "Insufficient data"
        ),
        "visual_data": None
    })

    return results


def driver_radar_chart(driver_row: pd.Series, driver_df: pd.DataFrame) -> go.Figure:
    metrics = {
        "Missing Rate": "missing_rate",
        "% Orders Missing": "pct_orders_with_missing",
        "Items Missing": "total_items_missing",
        "Avg Order Value": "avg_order_value",
        "Orders Completed": "total_orders",
    }

    values = []
    averages = []
    labels = list(metrics.keys())

    for label, col in metrics.items():
        series = driver_df[col].replace([np.inf, -np.inf], np.nan).fillna(0)
        min_val, max_val = series.min(), series.max()
        if max_val - min_val == 0:
            norm = 0
            avg_norm = 0
        else:
            norm = (driver_row[col] - min_val) / (max_val - min_val) * 100
            avg_norm = (series.mean() - min_val) / (max_val - min_val) * 100
        values.append(norm)
        averages.append(avg_norm)

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=labels,
        fill="toself",
        name=driver_row["driver_name"],
        line_color=COLORS["critical"] if driver_row["risk_category"] == "Critical" else COLORS["walmart_blue"]
    ))
    fig.add_trace(go.Scatterpolar(
        r=averages,
        theta=labels,
        fill="toself",
        name="Fleet Average",
        line_color=COLORS["success"],
        opacity=0.5
    ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        margin=dict(t=20, b=20, l=40, r=40),
        font_family=COLORS['font_family'],
        paper_bgcolor=COLORS['paper_bg'],
        showlegend=True
    )
    return fig


def build_monthly_trend_chart(monthly_df: pd.DataFrame, anomalies: dict, target_rate: float = 10.0) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=monthly_df["month_name"],
        y=monthly_df["orders"],
        name="Orders",
        marker_color=COLORS["walmart_blue_light"],
        opacity=0.6,
        text=monthly_df["orders"],
        textposition="outside",
        width=0.5,
        hovertemplate="%{x}: <b>%{y}</b> orders<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=monthly_df["month_name"],
        y=monthly_df["missing_rate"],
        name="Missing Rate",
        mode="lines+markers",
        marker=dict(size=7, color=COLORS["walmart_yellow"]),
        line=dict(width=3, shape="spline"),
        yaxis="y2",
        hovertemplate="%{x}: <b>%{y:.2f}%</b><extra></extra>"
    ))
    fig.update_layout(
        title="Orders vs Missing Rate (Monthly)",
        plot_bgcolor=COLORS['plot_bg'],
        paper_bgcolor=COLORS['paper_bg'],
        font_family=COLORS['font_family'],
        margin=dict(t=40, l=10, r=10, b=10),
        yaxis=dict(title="Orders", showgrid=True, gridcolor="rgba(243, 244, 246, 0.4)"),
        yaxis2=dict(title="Missing Rate (%)", overlaying="y", side="right", showgrid=False),
        xaxis_title=None,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    # Target line for easy interpretation
    fig.add_shape(
        type="line",
        x0=0,
        x1=1,
        xref="paper",
        y0=target_rate,
        y1=target_rate,
        yref="y2",
        line=dict(color=COLORS["warning"], width=2, dash="dash")
    )
    fig.add_annotation(
        x=0.99,
        xref="paper",
        y=target_rate,
        yref="y2",
        text=f"Target {target_rate:.1f}%",
        showarrow=False,
        font=dict(color=COLORS["warning"], size=11),
        xanchor="right",
        yanchor="bottom"
    )

    # Label key points (max/min/last)
    if not monthly_df.empty:
        max_idx = monthly_df["missing_rate"].idxmax()
        min_idx = monthly_df["missing_rate"].idxmin()
        last_row = monthly_df.iloc[-1]

        for _, row, label, color in [
            (max_idx, monthly_df.loc[max_idx], "Peak", COLORS["critical"]),
            (min_idx, monthly_df.loc[min_idx], "Minimum", COLORS["success"]),
            (None, last_row, "Latest", COLORS["walmart_blue"])
        ]:
            fig.add_annotation(
                x=row["month_name"],
                y=row["missing_rate"],
                yref="y2",
                text=f"{label}: {row['missing_rate']:.2f}%",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-28,
                font=dict(color=color, size=11)
            )

    # Contextual annotations
    if anomalies and anomalies.get("monthly"):
        month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for anomaly in anomalies["monthly"]:
            period = str(anomaly["period"])
            try:
                month_num = int(period.split("-")[1])
                month_label = month_names[month_num - 1]
            except Exception:
                month_label = period
            fig.add_annotation(
                x=month_label,
                y=anomaly["missing_rate"],
                text=f"Anomaly: {anomaly['missing_rate']:.2f}%",
                showarrow=True,
                arrowhead=2,
                ax=0,
                ay=-25,
                font=dict(color=COLORS["critical"], size=11)
            )

    return fig


def compute_cluster_analysis(driver_df: pd.DataFrame) -> dict:
    features = [
        "missing_rate",
        "pct_orders_with_missing",
        "avg_order_value",
        "total_orders",
        "total_items_missing",
        "trips"
    ]
    data = driver_df[features].replace([np.inf, -np.inf], np.nan).fillna(0)

    if len(data) < 6:
        return {"status": "insufficient"}

    scaler = StandardScaler()
    X = scaler.fit_transform(data)

    best_k = 2
    best_score = -1
    max_k = min(6, len(data) - 1)
    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(X)
        score = silhouette_score(X, labels)
        if score > best_score:
            best_k = k
            best_score = score

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X)

    clustered = driver_df.copy()
    clustered["cluster"] = labels

    cluster_stats = clustered.groupby("cluster").agg({
        "driver_id": "count",
        "missing_rate": "mean",
        "pct_orders_with_missing": "mean",
        "total_items_missing": "sum"
    }).reset_index().rename(columns={"driver_id": "drivers"})

    centers = kmeans.cluster_centers_
    variance = np.var(centers, axis=0)
    denom = (variance.max() - variance.min()) if variance.max() != variance.min() else 1
    importance = pd.DataFrame({
        "feature": features,
        "importance_score": (variance - variance.min()) / denom * 100
    }).sort_values("importance_score", ascending=False)

    return {
        "status": "ok",
        "silhouette": best_score,
        "n_clusters": best_k,
        "cluster_stats": cluster_stats,
        "clustered": clustered,
        "importance": importance
    }


def compute_regression_metrics(driver_df: pd.DataFrame) -> dict:
    features = ["trips", "age", "total_orders", "avg_order_value", "pct_orders_with_missing"]
    data = driver_df[features + ["missing_rate"]].replace([np.inf, -np.inf], np.nan).fillna(0)

    if len(data) < 10:
        return {"status": "insufficient"}

    X = data[features]
    y = data["missing_rate"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    model = LinearRegression()
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    return {
        "status": "ok",
        "r2": r2_score(y_test, preds),
        "rmse": float(np.sqrt(mean_squared_error(y_test, preds))),
        "coef": pd.DataFrame({"feature": features, "coef": model.coef_}).sort_values("coef", ascending=False)
    }


def correlation_strength(value: float) -> str:
    abs_val = abs(value)
    if abs_val >= 0.7:
        return "Strong"
    if abs_val >= 0.4:
        return "Moderate"
    if abs_val >= 0.2:
        return "Weak"
    return "Very weak"


def build_consistency_checks(
    orders_filtered: pd.DataFrame,
    monthly: pd.DataFrame,
    missing_rate: float,
    total_missing: float,
    total_items: float
) -> list:
    monthly_missing = float(monthly["items_missing"].sum()) if not monthly.empty else 0.0
    monthly_total_items = float(monthly["total_items"].sum()) if not monthly.empty else 0.0
    monthly_rate = (monthly_missing / monthly_total_items * 100) if monthly_total_items > 0 else 0.0
    null_critical = orders_filtered[["driver_id", "order_amount", "items_missing"]].isnull().any().any()

    checks = [
        {
            "dimension": "Reconciliation",
            "rule": "Missing items in the monthly series reconcile with the filtered total",
            "status": np.isclose(monthly_missing, total_missing),
            "current": f"{monthly_missing:.0f}",
            "reference": f"{total_missing:.0f}",
            "impact": "Prevents divergence between trend and aggregate KPI."
        },
        {
            "dimension": "Rate",
            "rule": "Aggregated monthly rate matches the Missing Rate KPI",
            "status": np.isclose(monthly_rate, missing_rate, atol=0.01),
            "current": f"{monthly_rate:.2f}%",
            "reference": f"{missing_rate:.2f}%",
            "impact": "Ensures denominator consistency across rate calculations."
        },
        {
            "dimension": "Sample",
            "rule": "Item volume remains valid after filters are applied",
            "status": total_items > 0,
            "current": f"{total_items:.0f}",
            "reference": "> 0",
            "impact": "Confirms visuals are not based on an empty sample."
        },
        {
            "dimension": "Completeness",
            "rule": "Critical fields contain no null values",
            "status": not null_critical,
            "current": "No nulls" if not null_critical else "Nulls detected",
            "reference": "No nulls",
            "impact": "Reduces distortion risk in operational metrics."
        },
    ]
    return checks


def render_consistency_table(checks: list) -> None:
    if not checks:
        st.info("No validation checks available for the selected period.")
        return

    ok_count = sum(1 for c in checks if c.get("status"))
    fail_count = len(checks) - ok_count

    rows_html = ""
    for c in checks:
        status_ok = bool(c.get("status"))
        status_label = "Pass" if status_ok else "Fail"
        status_class = "ok" if status_ok else "fail"
        dimension = escape(str(c.get("dimension", "-")))
        rule = escape(str(c.get("rule", "-")))
        current = escape(str(c.get("current", "-")))
        reference = escape(str(c.get("reference", "-")))
        impact = escape(str(c.get("impact", "-")))

        rows_html += f"""
        <tr class="{'fail-row' if not status_ok else ''}">
            <td>{dimension}</td>
            <td>{rule}</td>
            <td class="mono">{current}</td>
            <td class="mono">{reference}</td>
            <td><span class="status-pill {status_class}">{status_label}</span></td>
            <td>{impact}</td>
        </tr>
        """

    html = f"""
    <style>
      .cons-wrap {{
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        background: #fff;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
      }}
      .cons-head {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        padding: 13px 14px;
        border-bottom: 1px solid #e5e7eb;
        background: #fafbfc;
      }}
      .cons-title {{
        font-size: 14px;
        font-weight: 600;
        color: #111827;
        margin: 0 0 2px 0;
      }}
      .cons-sub {{
        font-size: 12px;
        color: #6b7280;
        margin: 0;
      }}
      .cons-kpis {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }}
      .cons-kpi {{
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        color: #4b5563;
      }}
      .cons-kpi.fail {{
        border-color: #fecaca;
        background: #fef2f2;
        color: #b91c1c;
      }}
      table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }}
      thead th {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .03em;
        color: #6b7280;
        font-weight: 600;
        padding: 11px 10px;
        border-bottom: 1px solid #e5e7eb;
        text-align: center;
      }}
      tbody td {{
        font-size: 12.5px;
        color: #1f2937;
        padding: 11px 10px;
        border-bottom: 1px solid #f3f4f6;
        text-align: center;
        vertical-align: middle;
      }}
      tbody tr:nth-child(even) {{
        background: #fcfcfd;
      }}
      tbody tr:last-child td {{
        border-bottom: none;
      }}
      tbody tr.fail-row {{
        background: #fffafb;
      }}
      .mono {{
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
        font-size: 12px;
        color: #4b5563;
      }}
      .status-pill {{
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        color: #374151;
      }}
      .status-pill.fail {{
        border-color: #fecaca;
        background: #fef2f2;
        color: #b91c1c;
      }}
    </style>
    <div class="cons-wrap">
      <div class="cons-head">
        <div>
          <p class="cons-title">Displayed Data Consistency Validation</p>
          <p class="cons-sub">Verifies that KPIs, trends, and filters share the same analytical base.</p>
        </div>
        <div class="cons-kpis">
          <span class="cons-kpi">Rules: {len(checks)}</span>
          <span class="cons-kpi">Passed: {ok_count}</span>
          <span class="cons-kpi fail">Failed: {fail_count}</span>
        </div>
      </div>
      <table>
        <thead>
          <tr>
            <th>Dimension</th>
            <th>Validation Rule</th>
            <th>Current</th>
            <th>Reference</th>
            <th>Status</th>
            <th>Impact</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """
    dynamic_height = 126 + (len(checks) * 42)
    components.html(html, height=dynamic_height, scrolling=False)


def render_detail_table(
    title: str,
    subtitle: str,
    dataframe: pd.DataFrame,
    summary_kpis: dict | None = None
) -> None:
    """Render a detailed table using the same visual language as consistency validation."""
    if dataframe.empty:
        st.info("Insufficient data to render the table.")
        return

    def _format_cell(value):
        if pd.isna(value):
            return "-"
        if isinstance(value, (bool, np.bool_)):
            return "Yes" if bool(value) else "No"
        if isinstance(value, (np.integer, int)):
            return f"{int(value):,}"
        if isinstance(value, (np.floating, float)):
            return f"{float(value):.4f}" if abs(float(value)) < 10 else f"{float(value):.2f}"
        return str(value)

    safe_df = dataframe.copy()
    headers = [escape(str(col)) for col in safe_df.columns]

    rows_html = ""
    for _, row in safe_df.iterrows():
        row_cells = "".join([f"<td>{escape(_format_cell(row[col]))}</td>" for col in safe_df.columns])
        rows_html += f"<tr>{row_cells}</tr>"

    kpis_html = ""
    if summary_kpis:
        kpis_html = "".join(
            [f"<span class='detail-kpi'>{escape(str(k))}: {escape(str(v))}</span>" for k, v in summary_kpis.items()]
        )

    html = f"""
    <style>
      .detail-wrap {{
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        overflow: hidden;
        background: #fff;
        margin-bottom: 12px;
      }}
      .detail-head {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 12px;
        padding: 12px 14px;
        border-bottom: 1px solid #e5e7eb;
        background: #fafbfc;
      }}
      .detail-title {{
        font-size: 14px;
        font-weight: 600;
        color: #111827;
        margin: 0 0 2px 0;
      }}
      .detail-sub {{
        font-size: 12px;
        color: #6b7280;
        margin: 0;
      }}
      .detail-kpis {{
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }}
      .detail-kpi {{
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid #e5e7eb;
        background: #f9fafb;
        color: #4b5563;
      }}
      .detail-wrap table {{
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
      }}
      .detail-wrap thead th {{
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: .03em;
        color: #6b7280;
        font-weight: 600;
        padding: 10px 8px;
        border-bottom: 1px solid #e5e7eb;
        text-align: center;
      }}
      .detail-wrap tbody td {{
        font-size: 12.5px;
        color: #1f2937;
        padding: 10px 8px;
        border-bottom: 1px solid #f3f4f6;
        text-align: center;
        vertical-align: middle;
      }}
      .detail-wrap tbody tr:nth-child(even) {{
        background: #fcfcfd;
      }}
      .detail-wrap tbody tr:last-child td {{
        border-bottom: none;
      }}
    </style>
    <div class="detail-wrap">
      <div class="detail-head">
        <div>
          <p class="detail-title">{escape(title)}</p>
          <p class="detail-sub">{escape(subtitle)}</p>
        </div>
        <div class="detail-kpis">{kpis_html}</div>
      </div>
      <table>
        <thead>
          <tr>
            {"".join([f"<th>{h}</th>" for h in headers])}
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
    """
    dynamic_height = 115 + (len(safe_df) * 38)
    components.html(html, height=dynamic_height, scrolling=False)


def detail_hint(label: str, text: str) -> str:
    """Build compact tooltip hint HTML for section subtitles."""
    safe_label = escape(label)
    safe_text = escape(text, quote=True)
    return (
        f"<span class='detail-hint'>"
        f"{safe_label}"
        f"<span class='detail-hint-icon' title='{safe_text}'>ⓘ</span>"
        f"</span>"
    )


def render_strategic_kpi(
    title: str,
    value: int | float | str,
    tooltip: str,
    color: str = COLORS["walmart_blue_light"],
    delta: str | None = None,
    delta_color: str = "normal",
) -> None:
    """Render KPI with backward compatibility for older kpi_card signatures."""
    params = inspect.signature(kpi_card).parameters
    if "card_class" in params:
        kwargs = {}
        if "color" in params:
            kwargs["color"] = color
        if "tooltip" in params:
            kwargs["tooltip"] = tooltip
        if "help_text" in params:
            kwargs["help_text"] = tooltip
        if "delta" in params and delta is not None:
            kwargs["delta"] = delta
        if "delta_color" in params and delta is not None:
            kwargs["delta_color"] = delta_color
        kwargs["card_class"] = "kpi-card--compact"
        kpi_card(title, value, **kwargs)
        return

    tooltip_attr = f'title="{escape(str(tooltip), quote=True)}"' if tooltip else ""
    info_icon = " ℹ️" if tooltip else ""
    cursor_style = "help" if tooltip else "default"

    delta_html = '<div class="kpi-meta"></div>'
    if delta is not None:
        is_pos = str(delta).startswith("+")
        if delta_color == "inverse":
            d_class = "delta-neg" if is_pos else "delta-pos"
        elif delta_color == "normal":
            d_class = "delta-pos" if is_pos else "delta-neg"
        else:
            d_class = "delta-neu"
        delta_html = f'<div class="kpi-meta"><span class="{d_class}">{escape(str(delta))}</span></div>'

    st.markdown(
        f"""
        <div class="kpi-card kpi-card--compact" style="border-left-color: {color}; cursor: {cursor_style};" {tooltip_attr}>
            <div class="kpi-title">{escape(str(title))}{info_icon}</div>
            <div class="kpi-value">{escape(str(value))}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    render_sidebar()
    st.markdown(
        """
        <style>
            .drivers-context-strip {
                display: flex;
                flex-wrap: wrap;
                gap: 0.5rem;
                margin-bottom: 0.85rem;
            }
            .drivers-context-pill {
                background: #eef2ff;
                border: 1px solid #dbeafe;
                color: #1e3a8a;
                font-size: 0.78rem;
                font-weight: 600;
                border-radius: 999px;
                padding: 0.24rem 0.65rem;
            }
            .drivers-context-note {
                font-size: 0.82rem;
                color: #475569;
                margin-bottom: 0.75rem;
            }
            .detail-hint {
                font-size: 0.82rem;
                color: #64748b;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 0.35rem;
            }
            .detail-hint-icon {
                width: 1.05rem;
                height: 1.05rem;
                border-radius: 999px;
                border: 1px solid #cbd5e1;
                color: #334155;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                font-size: 0.68rem;
                background: #ffffff;
                cursor: help;
            }
            .relation-grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.65rem;
                margin: 0.4rem 0 0.8rem;
            }
            .relation-card {
                background: #ffffff;
                border: 1px solid #e5e7eb;
                border-radius: 10px;
                padding: 0.75rem 0.8rem;
                box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
            }
            .relation-rank {
                font-size: 0.72rem;
                color: #64748b;
                text-transform: uppercase;
                font-weight: 700;
                letter-spacing: 0.04em;
                margin-bottom: 0.2rem;
            }
            .relation-title {
                font-size: 0.86rem;
                font-weight: 650;
                color: #0f172a;
                line-height: 1.25;
                margin-bottom: 0.45rem;
            }
            .relation-meta {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 0.45rem;
            }
            .relation-chip {
                font-size: 0.72rem;
                font-weight: 700;
                border-radius: 999px;
                padding: 0.16rem 0.5rem;
                border: 1px solid transparent;
            }
            .chip-pos {
                color: #166534;
                background: #dcfce7;
                border-color: #bbf7d0;
            }
            .chip-neg {
                color: #9f1239;
                background: #ffe4e6;
                border-color: #fecdd3;
            }
            .chip-strong {
                color: #1d4ed8;
                background: #dbeafe;
                border-color: #bfdbfe;
            }
            .chip-medium {
                color: #92400e;
                background: #fef3c7;
                border-color: #fde68a;
            }
            .chip-light {
                color: #475569;
                background: #f1f5f9;
                border-color: #e2e8f0;
            }
            .audience-temporal-title {
                margin-top: 1.15rem;
                margin-bottom: 0.22rem;
            }
            .audience-temporal-caption {
                margin: 0 0 0.85rem 0;
                font-size: 0.82rem;
                color: #64748b;
            }
            .monitor-summary {
                margin-top: 0.52rem;
                margin-bottom: 1.05rem;
                border: 1px solid #dbeafe;
                border-left: 4px solid #2563eb;
                border-radius: 10px;
                background: #f8fbff;
                padding: 0.52rem 0.72rem;
                display: flex;
                align-items: center;
                gap: 0.45rem;
                line-height: 1.35;
            }
            .monitor-summary-label {
                font-size: 0.74rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.03em;
                color: #1d4ed8;
                background: #dbeafe;
                border-radius: 999px;
                padding: 0.12rem 0.46rem;
                white-space: nowrap;
            }
            .monitor-summary-text {
                font-size: 0.86rem;
                color: #0f172a;
                font-weight: 520;
            }
            .monitor-summary--success {
                border-color: #bbf7d0;
                border-left-color: #10b981;
                background: #f0fdf4;
            }
            .monitor-summary--success .monitor-summary-label {
                color: #047857;
                background: #dcfce7;
            }
            .monitoring-gap {
                height: 0.4rem;
            }
            @media (max-width: 1200px) {
                .relation-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }
            @media (max-width: 760px) {
                .relation-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown("### Operational Intelligence")
    st.markdown(f"""
    <div class="dashboard-header-row">
        <div>
            <h1 style="margin:0; font-size: 2.5rem;">Driver Intelligence Monitor</h1>
            <p class="text-muted">Continuous monitoring of driver performance and risk.</p>
        </div>
        <div class="scope-badge-container">
             <span class="badge badge-success">System Online</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    orders, drivers, drivers_summary = load_base_data()

    # ------------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------------
    st.markdown("#### Operational Filters")
    min_date = orders["order_date"].min().date() if not orders.empty else date.today()
    max_date = orders["order_date"].max().date() if not orders.empty else date.today()

    f1, f2, f3, f4 = st.columns([1.5, 1, 1, 1.5])
    with f1:
        date_range = st.date_input("Period", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    with f2:
        risk_filter = st.multiselect("Risk", ["Critical", "High", "Medium", "Low"], default=["Critical", "High"])
    with f3:
        experience_filter = st.multiselect("Experience", ["Novice", "Intermediate", "Experienced", "Expert"])
    with f4:
        region_filter = st.multiselect("Region", sorted(orders["region"].dropna().unique().tolist()))

    search = st.text_input("Search driver (name or ID)", placeholder="WDID...")

    # Filter orders by date/region
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    orders_filtered = orders[
        (orders["order_date"].dt.date >= start_date) &
        (orders["order_date"].dt.date <= end_date)
    ].copy()

    if region_filter:
        orders_filtered = orders_filtered[orders_filtered["region"].isin(region_filter)]

    driver_snapshot = build_driver_snapshot(orders_filtered, drivers)

    if experience_filter:
        driver_snapshot = driver_snapshot[driver_snapshot["experience_level"].isin(experience_filter)]

    if risk_filter:
        driver_snapshot = driver_snapshot[driver_snapshot["risk_category"].isin(risk_filter)]

    if search:
        driver_snapshot = driver_snapshot[
            driver_snapshot["driver_name"].str.contains(search, case=False, na=False) |
            driver_snapshot["driver_id"].str.contains(search, case=False, na=False)
        ]

    if driver_snapshot.empty:
        st.warning("No drivers found for the current filters.")
        return

    # ------------------------------------------------------------------
    # Executive Summary
    # ------------------------------------------------------------------
    st.markdown("#### Executive Summary")
    total_items = orders_filtered["items_delivered"].sum() + orders_filtered["items_missing"].sum()
    total_missing = orders_filtered["items_missing"].sum()
    missing_rate = (total_missing / total_items * 100) if total_items > 0 else 0
    active_drivers = orders_filtered["driver_id"].nunique()

    critical_drivers = driver_snapshot[driver_snapshot["risk_category"] == "Critical"]["driver_id"].unique()
    optimized_orders = orders_filtered[~orders_filtered["driver_id"].isin(critical_drivers)]
    optimized_items = optimized_orders["items_delivered"].sum() + optimized_orders["items_missing"].sum()
    optimized_missing = optimized_orders["items_missing"].sum()
    optimized_rate = (optimized_missing / optimized_items * 100) if optimized_items > 0 else 0
    savings_proxy = max(missing_rate - optimized_rate, 0) / 100 * total_items * ITEM_VALUE_USD

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_strategic_kpi(
            "Drivers Ativos",
            int(active_drivers),
            tooltip="Drivers with deliveries in the selected period.",
        )
    with k2:
        render_strategic_kpi(
            "Missing Rate",
            f"{missing_rate:.2f}%",
            tooltip="Percentage of missing items over total items in the selected period.",
            delta=f"{missing_rate - optimized_rate:+.2f}pp",
            delta_color="inverse",
        )
    with k3:
        render_strategic_kpi(
            "Critical Drivers",
            int(len(critical_drivers)),
            tooltip="Drivers classified as critical risk in the selected period.",
        )
    with k4:
        render_strategic_kpi(
            "Estimated Loss",
            f"${total_missing * ITEM_VALUE_USD:,.0f}",
            tooltip="Financial estimate: missing items multiplied by USD 15.",
        )
    with k5:
        render_strategic_kpi(
            "Potential Impact",
            f"${savings_proxy:,.0f}",
            tooltip="Potential savings in the scenario without critical drivers.",
            color=COLORS["success"],
        )

    # ------------------------------------------------------------------
    # Storytelling
    # ------------------------------------------------------------------
    st.markdown("#### Monitoring Narrative")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        insight_card("Problem", "Recurring delivery losses impact margin and customer trust.")
    with s2:
        insight_card("Approach", "Hypotheses tested with statistics, segmentation, and time series.")
    with s3:
        insight_card("Findings", "Critical drivers and periods concentrate missing-rate peaks.")
    with s4:
        insight_card("Impact", "Focused interventions reduce exposure and prioritize auditing.")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Hypotheses & Methods
    # ------------------------------------------------------------------
    st.markdown("#### Hypotheses & Analytical Strategies")

    # Prefer session-cached hypotheses (shared with Monitor page), fallback to local recomputation.
    if "drivers_hypotheses" not in st.session_state:
        try:
            st.session_state["drivers_hypotheses"] = get_default_cache().get_hypothesis_results()
        except Exception:
            st.session_state["drivers_hypotheses"] = []

    hypotheses = st.session_state.get("drivers_hypotheses") or compute_hypotheses(
        orders_filtered, drivers, driver_snapshot
    )

    status_map = {
        "Validated": ("✅", COLORS["success"]),
        "Investigating": ("⏳", COLORS["warning"]),
        "Rejected": ("❌", COLORS["critical"]),
    }

    h_cols = st.columns(2)
    for idx, h in enumerate(hypotheses):
        icon, status_color = status_map.get(h.get("status", "Investigating"), ("❓", "#6b7280"))
        with h_cols[idx % 2]:
            with st.container(border=True):
                left, right = st.columns([4, 1])
                with left:
                    st.markdown(f"**{h.get('id', '-')}: {h.get('statement', '-') }**")
                with right:
                    st.markdown(
                        f"<div style='text-align:right;color:{status_color};font-weight:700;'>{icon} {h.get('status','-')}</div>",
                        unsafe_allow_html=True
                    )

                st.write(h.get("result_text", "No result"))

                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    st.caption("Method")
                    st.write(h.get("methodology", "-"))
                with meta_col2:
                    st.caption(h.get("metric_name", "Metric"))
                    metric_val = h.get("metric_value")
                    if isinstance(metric_val, (int, float, np.number)) and np.isfinite(float(metric_val)):
                        st.write(f"{float(metric_val):.3f}")
                    else:
                        st.write("-")
                with meta_col3:
                    st.caption("p-value")
                    p_val = h.get("p_value")
                    if isinstance(p_val, (int, float, np.number)) and np.isfinite(float(p_val)):
                        st.write(f"{float(p_val):.4f}")
                    else:
                        st.write("-")

    st.markdown("---")

    # ------------------------------------------------------------------
    # Monitoring Visuals
    # ------------------------------------------------------------------
    st.markdown("#### Monitoring & Evidence")
    region_label = ", ".join(region_filter) if region_filter else "All"
    st.markdown(
        f"""
        <div class="drivers-context-strip">
            <span class="drivers-context-pill">Period: {start_date.strftime('%Y-%m-%d')} → {end_date.strftime('%Y-%m-%d')}</span>
            <span class="drivers-context-pill">Regions: {escape(region_label)}</span>
            <span class="drivers-context-pill">Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    monthly = orders_filtered.groupby("month").agg({
        "order_id": "count",
        "items_delivered": "sum",
        "items_missing": "sum"
    }).reset_index().sort_values("month")
    monthly = monthly.rename(columns={"order_id": "orders"})
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly["month_name"] = monthly["month"].apply(lambda x: month_names[x-1])
    monthly["total_items"] = monthly["items_delivered"] + monthly["items_missing"]
    monthly["missing_rate"] = np.where(
        monthly["total_items"] > 0,
        (monthly["items_missing"] / monthly["total_items"]) * 100,
        0
    )

    anomalies = detect_temporal_anomalies(orders_filtered)
    trend_fig = build_monthly_trend_chart(monthly, anomalies, target_rate=10.0)
    checks = build_consistency_checks(orders_filtered, monthly, missing_rate, total_missing, total_items)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.markdown(
            detail_hint(
                "Monthly trend",
                "Bars represent order volume; line represents monthly missing rate."
            ),
            unsafe_allow_html=True
        )
        st.plotly_chart(trend_fig, use_container_width=True, key="drivers_trend_main")
        if not monthly.empty:
            last = monthly.iloc[-1]
            prev = monthly.iloc[-2] if len(monthly) > 1 else last
            delta_pp = last["missing_rate"] - prev["missing_rate"]
            st.markdown(
                (
                    "<div class='monitor-summary'>"
                    "<span class='monitor-summary-label'>Summary</span>"
                    f"<span class='monitor-summary-text'>Last month at <strong>{last['missing_rate']:.2f}%</strong> "
                    f"({delta_pp:+.2f} pp vs previous month).</span>"
                    "</div>"
                ),
                unsafe_allow_html=True
            )
    with c2:
        st.markdown(
            detail_hint(
                "Scenario comparison",
                "Compares current missing rate with a hypothetical scenario without critical drivers."
            ),
            unsafe_allow_html=True
        )
        comparison_df = pd.DataFrame({
            "scenario": ["Baseline", "Without critical drivers"],
            "missing_rate": [missing_rate, optimized_rate]
        })
        comp_fig = px.bar(
            comparison_df,
            x="scenario",
            y="missing_rate",
            title="Baseline vs Mitigado",
            color="scenario",
            color_discrete_sequence=[COLORS["walmart_blue"], COLORS["success"]],
            text="missing_rate"
        )
        comp_fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        comp_fig.update_layout(
            plot_bgcolor=COLORS['plot_bg'],
            paper_bgcolor=COLORS['paper_bg'],
            font_family=COLORS['font_family'],
            yaxis_title="Missing Rate (%)",
            xaxis_title=None,
            showlegend=False
        )
        st.plotly_chart(comp_fig, use_container_width=True, key="drivers_baseline_vs_mitigated")
        st.markdown(
            (
                "<div class='monitor-summary monitor-summary--success'>"
                "<span class='monitor-summary-label'>Summary</span>"
                f"<span class='monitor-summary-text'>Intervention on critical drivers reduces rate by "
                f"<strong>{(missing_rate - optimized_rate):.2f} pp</strong>.</span>"
                "</div>"
            ),
            unsafe_allow_html=True
        )

    st.markdown("<div class='monitoring-gap'></div>", unsafe_allow_html=True)
    render_consistency_table(checks)

    # Correlation Heatmap
    numeric_cols = driver_snapshot.select_dtypes(include=[np.number]).columns
    corr_df = driver_snapshot[numeric_cols].corr().fillna(0).round(2)
    st.markdown("#### Correlations Between Key Variables")
    st.markdown(
        detail_hint(
            "Correlation matrix",
            "Values close to +1 or -1 indicate strong relationships between metrics."
        ),
        unsafe_allow_html=True
    )
    plot_correlation_heatmap(corr_df, "Driver Metrics Correlation", key="drivers_corr_heatmap")

    # Top correlation narrative (exclude self-correlation)
    upper = corr_df.where(np.triu(np.ones(corr_df.shape), k=1).astype(bool))
    pairs = (
        upper.stack()
        .reset_index()
        .rename(columns={"level_0": "var_1", "level_1": "var_2", 0: "corr"})
    )
    top_pairs = pairs.reindex(pairs["corr"].abs().sort_values(ascending=False).index).head(3).copy()
    if not top_pairs.empty:
        top_pairs["strength"] = top_pairs["corr"].apply(correlation_strength)
        st.markdown("**Top 3 relationships for quick interpretation**")

        strength_class = {
            "Strong": "chip-strong",
            "Moderate": "chip-medium",
            "Weak": "chip-light",
            "Very weak": "chip-light",
        }
        cards_html = ["<div class='relation-grid'>"]
        for i, (_, r) in enumerate(top_pairs.iterrows(), start=1):
            relation_title = escape(f"{r['var_1']} × {r['var_2']}")
            corr_val = float(r["corr"])
            signal_class = "chip-pos" if corr_val >= 0 else "chip-neg"
            signal_label = "Positive" if corr_val >= 0 else "Negative"
            strength = str(r["strength"])
            cards_html.append(
                (
                    f"<div class='relation-card'>"
                    f"<div class='relation-rank'>Relationship #{i}</div>"
                    f"<div class='relation-title'>{relation_title}</div>"
                    f"<div class='relation-meta'>"
                    f"<span class='relation-chip {signal_class}'>{signal_label}: {corr_val:.2f}</span>"
                    f"<span class='relation-chip {strength_class.get(strength, 'chip-light')}'>{escape(strength)}</span>"
                    f"</div>"
                    f"</div>"
                )
            )
        cards_html.append("</div>")
        st.markdown("".join(cards_html), unsafe_allow_html=True)

    st.markdown("---")

    # ------------------------------------------------------------------
    # Audience Modules
    # ------------------------------------------------------------------
    st.markdown("#### Audience Views")
    tabs = st.tabs(["Executives", "Technical Managers", "Analysts", "Business Stakeholders"])

    # Executives
    with tabs[0]:
        st.markdown("**Strategic KPIs**")
        kpi_cols = st.columns(4)
        with kpi_cols[0]:
            render_strategic_kpi(
                "Exposure",
                f"${total_missing * ITEM_VALUE_USD:,.0f}",
                tooltip="Estimated financial loss from missing items in the filtered period.",
            )
        with kpi_cols[1]:
            render_strategic_kpi(
                "Drivers at Risk",
                int(driver_snapshot[driver_snapshot["risk_category"].isin(["High", "Critical"])].shape[0]),
                tooltip="Number of drivers classified as High or Critical under current filters.",
            )
        with kpi_cols[2]:
            render_strategic_kpi(
                "Missing Rate",
                f"{missing_rate:.2f}%",
                tooltip="Percentage of missing items over total delivered items in the selected period.",
            )
        with kpi_cols[3]:
            render_strategic_kpi(
                "Potential Impact",
                f"${savings_proxy:,.0f}",
                tooltip="Potential savings if current rate converges to the scenario without critical drivers.",
                color=COLORS["success"],
            )

        st.markdown(
            "<div class='audience-temporal-title'><strong>Temporal Comparison</strong></div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p class='audience-temporal-caption'>Same temporal comparison from the main panel for executive reading.</p>",
            unsafe_allow_html=True,
        )
        st.plotly_chart(trend_fig, use_container_width=True, key="drivers_trend_exec")

    # Technical Managers
    with tabs[1]:
        st.markdown("**Pipeline & Model Metrics**")
        perf = get_default_cache().get_model_performance_metrics()

        st.markdown(f"- Algoritmo: `{perf['model_info']['algorithm']}`")
        st.markdown(f"- Features monitoradas: {', '.join(perf['model_info']['features'])}")
        st.caption("Unsupervised model: performance monitored through anomaly stability and drift.")

        perf_cols = st.columns(2)
        with perf_cols[0]:
            st.markdown("**Drift by Feature**")
            drift_df = pd.DataFrame(perf["drift_analysis"])
            if not drift_df.empty:
                st.dataframe(drift_df[["feature", "ks_stat", "p_value", "is_drifting"]], use_container_width=True)
        with perf_cols[1]:
            st.markdown("**Stability Proxy**")
            st.markdown(f"- Reference anomaly rate: {perf['performance']['reference_anomaly_rate']:.2f}%")
            st.markdown(f"- Current anomaly rate: {perf['performance']['current_anomaly_rate']:.2f}%")
            st.markdown(f"- Status: **{perf['performance']['status']}**")

    # Analysts
    with tabs[2]:
        st.markdown("**Technical Drill-down**")

        driver_options = driver_snapshot.apply(
            lambda r: f"{r['driver_name']} ({r['driver_id']})", axis=1
        ).tolist()
        selected_label = st.selectbox("Select driver", driver_options)
        selected_id = selected_label.split("(")[-1].replace(")", "")
        driver_row = driver_snapshot[driver_snapshot["driver_id"] == selected_id].iloc[0]

        d1, d2 = st.columns([1.2, 1])
        with d1:
            st.markdown(f"**{driver_row['driver_name']}**")
            st.markdown(f"ID: `{driver_row['driver_id']}`")
            risk_badge(str(driver_row["risk_category"]))

            st.markdown("**Key metrics**")
            st.markdown(f"- Orders: {int(driver_row['total_orders'])}")
            st.markdown(f"- Missing rate: {driver_row['missing_rate']:.2f}%")
            st.markdown(f"- % Orders missing: {driver_row['pct_orders_with_missing']:.2f}%")
            st.markdown(f"- Missing value: ${driver_row['missing_value']:,.0f}")

        with d2:
            st.caption("Tooltip: driver profile versus fleet average (normalized 0-100 scale).")
            st.plotly_chart(
                driver_radar_chart(driver_row, driver_snapshot),
                use_container_width=True,
                key=f"drivers_radar_{selected_id}"
            )

        monthly_driver = build_driver_monthly(orders_filtered)
        driver_month = monthly_driver[monthly_driver["driver_id"] == selected_id]
        if not driver_month.empty:
            fig_driver = px.line(
                driver_month,
                x="month_name",
                y="missing_rate",
                title="Missing Rate by Month",
                markers=True,
                color_discrete_sequence=[COLORS["walmart_blue_light"]]
            )
            fig_driver.update_layout(plot_bgcolor=COLORS['plot_bg'], paper_bgcolor=COLORS['paper_bg'], font_family=COLORS['font_family'])
            st.caption("Tooltip: monthly missing-rate evolution for the selected driver.")
            st.plotly_chart(fig_driver, use_container_width=True, key=f"drivers_monthly_{selected_id}")

        st.markdown("**Distribution and Outliers**")
        comparison_df, stats_summary = compare_driver_performance(driver_snapshot)
        outliers = comparison_df[comparison_df["is_outlier"]]
        st.markdown(f"Drivers outliers: {len(outliers)}")
        st.caption("Outliers are defined as missing rate > mean + 2 standard deviations.")
        st.dataframe(outliers[["driver_id", "driver_name", "missing_rate", "total_orders"]].head(20), use_container_width=True)

    # Business stakeholders
    with tabs[3]:
        st.markdown("**Comparisons and Benchmarks**")
        region_summary = orders_filtered.groupby("region").agg({
            "items_delivered": "sum",
            "items_missing": "sum",
            "order_id": "count"
        }).reset_index()
        region_summary["total_items"] = region_summary["items_delivered"] + region_summary["items_missing"]
        region_summary["missing_rate"] = np.where(
            region_summary["total_items"] > 0,
            (region_summary["items_missing"] / region_summary["total_items"]) * 100,
            0
        )
        region_summary = region_summary.sort_values("missing_rate", ascending=False)

        fig_region = px.bar(
            region_summary,
            x="region",
            y="missing_rate",
            title="Missing Rate by Region",
            color="missing_rate",
            color_continuous_scale="Reds"
        )
        fig_region.update_layout(plot_bgcolor=COLORS['plot_bg'], paper_bgcolor=COLORS['paper_bg'], font_family=COLORS['font_family'])
        st.caption("Tooltip: regional benchmark for operational prioritization.")
        st.plotly_chart(fig_region, use_container_width=True, key="drivers_region_benchmark")

        st.markdown("**Highest Impact Segments**")
        segment_exp = driver_snapshot.groupby("experience_level").agg({
            "driver_id": "count",
            "missing_value": "sum",
            "missing_rate": "mean"
        }).reset_index().rename(columns={"driver_id": "drivers"})
        total_missing_value = segment_exp["missing_value"].sum()
        segment_exp["missing_share"] = (
            segment_exp["missing_value"] / total_missing_value * 100 if total_missing_value > 0 else 0
        )
        segment_exp = segment_exp.sort_values("missing_share", ascending=False)
        st.dataframe(segment_exp, use_container_width=True)

        st.markdown("**Impact Translation**")
        st.markdown(
            f"- Reducing missing rate from {missing_rate:.2f}% to {optimized_rate:.2f}% avoids ~${savings_proxy:,.0f} in annual losses (proxy)."
        )

    st.markdown("---")

    # ------------------------------------------------------------------
    # Advanced Analytics (Load on Demand)
    # ------------------------------------------------------------------
    st.markdown("#### Advanced Analytics (Load-on-Demand)")
    if st.toggle("Load advanced analytics"):
        cluster = compute_cluster_analysis(driver_snapshot)
        regression = compute_regression_metrics(driver_snapshot)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Clustering & Silhouette**")
            st.caption("Silhouette measures separation between clusters (0 to 1).")
            if cluster["status"] == "ok":
                cluster_table = cluster["cluster_stats"].copy()
                cluster_table["cluster"] = cluster_table["cluster"].apply(lambda c: f"C{int(c)}")
                cluster_table = cluster_table.rename(
                    columns={
                        "cluster": "Cluster",
                        "drivers": "Drivers",
                        "missing_rate": "Missing Rate (%)",
                        "pct_orders_with_missing": "Orders with Missing (%)",
                        "total_items_missing": "Missing Items",
                    }
                )
                render_detail_table(
                    title="Cluster Summary",
                    subtitle="Driver segmentation by risk profile and operational volume.",
                    dataframe=cluster_table,
                    summary_kpis={
                        "Clusters": cluster["n_clusters"],
                        "Silhouette": f"{cluster['silhouette']:.3f}",
                        "Drivers": int(cluster_table["Drivers"].sum()),
                    }
                )

                importance_fig = px.bar(
                    cluster["importance"],
                    x="importance_score",
                    y="feature",
                    orientation="h",
                    title="Feature Importance (Cluster Variance)",
                    color_discrete_sequence=[COLORS["walmart_blue_light"]]
                )
                importance_fig.update_layout(plot_bgcolor=COLORS['plot_bg'], paper_bgcolor=COLORS['paper_bg'], font_family=COLORS['font_family'])
                st.caption("Tooltip: relative importance by cluster separation.")
                st.plotly_chart(importance_fig, use_container_width=True, key="drivers_cluster_importance")
            else:
                st.info("Insufficient data for clustering.")

        with c2:
            st.markdown("**Regression & Validation**")
            st.caption("R² indicates explained variance; RMSE is average error in percentage points.")
            if regression["status"] == "ok":
                coef_table = regression["coef"].copy()
                coef_table["direction"] = coef_table["coef"].apply(lambda c: "Positive" if c >= 0 else "Negative")
                coef_table["coef"] = coef_table["coef"].apply(lambda c: f"{c:+.4f}")
                coef_table = coef_table.rename(
                    columns={
                        "feature": "Feature",
                        "coef": "Coefficient",
                        "direction": "Direction",
                    }
                )
                render_detail_table(
                    title="Regression Coefficients",
                    subtitle="Contribution of each feature to explain missing-rate variation.",
                    dataframe=coef_table,
                    summary_kpis={
                        "R²": f"{regression['r2']:.3f}",
                        "RMSE": f"{regression['rmse']:.3f}",
                        "Features": len(coef_table),
                    }
                )
            else:
                st.info("Insufficient data for regression.")

    # ------------------------------------------------------------------
    # Detailed Tables & Export
    # ------------------------------------------------------------------
    st.markdown("#### Detailed Tables")
    detail_df = (
        driver_snapshot[
            [
                "driver_id",
                "driver_name",
                "risk_category",
                "total_orders",
                "missing_rate",
                "pct_orders_with_missing",
                "avg_order_value",
                "missing_value",
            ]
        ]
        .sort_values("missing_rate", ascending=False)
        .rename(
            columns={
                "driver_id": "Driver ID",
                "driver_name": "Driver",
                "risk_category": "Risk",
                "total_orders": "Orders",
                "missing_rate": "Missing Rate (%)",
                "pct_orders_with_missing": "Orders with Missing (%)",
                "avg_order_value": "Average Ticket (USD)",
                "missing_value": "Estimated Loss (USD)",
            }
        )
    )
    row_cap = min(60, len(detail_df)) if len(detail_df) else 0
    if row_cap > 0:
        render_detail_table(
            title="Detailed Driver Ranking",
            subtitle=f"Showing the top {row_cap} drivers with highest missing rate in the filtered period.",
            dataframe=detail_df.head(row_cap),
            summary_kpis={
                "Drivers": len(detail_df),
                "Average Missing": f"{detail_df['Missing Rate (%)'].mean():.2f}%",
                "Critical": int((detail_df["Risk"] == "Critical").sum()),
            },
        )
    else:
        st.info("No data available for detailed ranking display.")

if __name__ == "__main__":
    main()

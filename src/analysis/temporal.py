"""
Temporal analysis for time-based fraud patterns.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple


def analyze_monthly_trends(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze monthly trends in orders and missing items.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with monthly trends
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.to_period("M")

    monthly = df.groupby("month").agg({
        "order_id": "count",
        "order_amount": ["sum", "mean"],
        "items_delivered": "sum",
        "items_missing": "sum",
        "driver_id": "nunique",
        "customer_id": "nunique",
    }).reset_index()

    monthly.columns = [
        "month", "total_orders", "total_revenue", "avg_order_value",
        "items_delivered", "items_missing", "unique_drivers", "unique_customers"
    ]

    monthly["total_items"] = monthly["items_delivered"] + monthly["items_missing"]
    monthly["missing_rate"] = np.where(
        monthly["total_items"] > 0,
        monthly["items_missing"] / monthly["total_items"] * 100,
        0
    )

    # Calculate month-over-month changes
    monthly["orders_mom"] = monthly["total_orders"].pct_change() * 100
    monthly["revenue_mom"] = monthly["total_revenue"].pct_change() * 100
    monthly["missing_rate_change"] = monthly["missing_rate"].diff()

    # Orders with missing items
    orders_with_missing = df[df["items_missing"] > 0].groupby("month").size()
    monthly["orders_with_missing"] = monthly["month"].map(orders_with_missing).fillna(0).astype(int)
    monthly["pct_orders_with_missing"] = (
        monthly["orders_with_missing"] / monthly["total_orders"] * 100
    )

    return monthly


def analyze_weekly_patterns(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze weekly patterns in orders.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with weekly patterns
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["week"] = df["order_date"].dt.to_period("W")

    weekly = df.groupby("week").agg({
        "order_id": "count",
        "order_amount": "sum",
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    weekly.columns = [
        "week", "total_orders", "total_revenue",
        "items_delivered", "items_missing"
    ]

    weekly["total_items"] = weekly["items_delivered"] + weekly["items_missing"]
    weekly["missing_rate"] = np.where(
        weekly["total_items"] > 0,
        weekly["items_missing"] / weekly["total_items"] * 100,
        0
    )

    return weekly


def analyze_day_of_week_patterns(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze patterns by day of week.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with day of week patterns
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["day_num"] = df["order_date"].dt.dayofweek

    daily = df.groupby(["day_num", "day_of_week"]).agg({
        "order_id": "count",
        "order_amount": ["sum", "mean"],
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    daily.columns = [
        "day_num", "day_of_week", "total_orders", "total_revenue",
        "avg_order_value", "items_delivered", "items_missing"
    ]

    daily["total_items"] = daily["items_delivered"] + daily["items_missing"]
    daily["missing_rate"] = np.where(
        daily["total_items"] > 0,
        daily["items_missing"] / daily["total_items"] * 100,
        0
    )
    daily["is_weekend"] = daily["day_num"] >= 5

    return daily.sort_values("day_num")


def analyze_hourly_patterns(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze patterns by hour of day.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with hourly patterns
    """
    df = orders_df.copy()

    # Extract hour from delivery_hour
    df["hour"] = pd.to_datetime(
        df["delivery_hour"].astype(str), format="%H:%M:%S", errors="coerce"
    ).dt.hour

    hourly = df.groupby("hour").agg({
        "order_id": "count",
        "order_amount": "mean",
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    hourly.columns = [
        "hour", "total_orders", "avg_order_value",
        "items_delivered", "items_missing"
    ]

    hourly["total_items"] = hourly["items_delivered"] + hourly["items_missing"]
    hourly["missing_rate"] = np.where(
        hourly["total_items"] > 0,
        hourly["items_missing"] / hourly["total_items"] * 100,
        0
    )

    # Add period labels
    hourly["period"] = pd.cut(
        hourly["hour"],
        bins=[-1, 6, 12, 18, 24],
        labels=["Night (0-6)", "Morning (6-12)", "Afternoon (12-18)", "Evening (18-24)"]
    )

    return hourly


def detect_temporal_anomalies(
    orders_df: pd.DataFrame,
    threshold_std: float = 2.0
) -> Dict[str, Any]:
    """
    Detect temporal anomalies in the data.

    Args:
        orders_df: Orders DataFrame
        threshold_std: Standard deviations for anomaly detection

    Returns:
        Dictionary with detected anomalies
    """
    anomalies = {
        "monthly": [],
        "daily": [],
        "hourly": [],
    }

    # Monthly anomalies
    monthly = analyze_monthly_trends(orders_df)
    avg = monthly["missing_rate"].mean()
    std = monthly["missing_rate"].std()
    threshold = avg + threshold_std * std

    for _, row in monthly[monthly["missing_rate"] > threshold].iterrows():
        anomalies["monthly"].append({
            "period": str(row["month"]),
            "missing_rate": row["missing_rate"],
            "threshold": threshold,
            "deviation": (row["missing_rate"] - avg) / std if std > 0 else 0
        })

    # Daily anomalies
    daily = analyze_day_of_week_patterns(orders_df)
    avg = daily["missing_rate"].mean()
    std = daily["missing_rate"].std()
    threshold = avg + threshold_std * std

    for _, row in daily[daily["missing_rate"] > threshold].iterrows():
        anomalies["daily"].append({
            "day": row["day_of_week"],
            "missing_rate": row["missing_rate"],
            "threshold": threshold,
            "is_weekend": row["is_weekend"]
        })

    # Hourly anomalies
    hourly = analyze_hourly_patterns(orders_df)
    avg = hourly["missing_rate"].mean()
    std = hourly["missing_rate"].std()
    threshold = avg + threshold_std * std

    for _, row in hourly[hourly["missing_rate"] > threshold].iterrows():
        anomalies["hourly"].append({
            "hour": int(row["hour"]),
            "period": str(row["period"]),
            "missing_rate": row["missing_rate"],
            "threshold": threshold
        })

    return anomalies


def analyze_trend_direction(orders_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyze if fraud is trending up or down over time.

    Args:
        orders_df: Orders DataFrame

    Returns:
        Dictionary with trend analysis
    """
    monthly = analyze_monthly_trends(orders_df)

    # Calculate linear regression slope for missing rate
    x = np.arange(len(monthly))
    y = monthly["missing_rate"].values

    # Simple linear regression
    if len(x) > 1:
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0

    # First vs last period comparison
    first_period = monthly.iloc[:3]["missing_rate"].mean() if len(monthly) >= 3 else monthly.iloc[0]["missing_rate"]
    last_period = monthly.iloc[-3:]["missing_rate"].mean() if len(monthly) >= 3 else monthly.iloc[-1]["missing_rate"]

    trend = {
        "slope": slope,
        "direction": "increasing" if slope > 0.1 else "decreasing" if slope < -0.1 else "stable",
        "first_period_avg": first_period,
        "last_period_avg": last_period,
        "change_pct": (last_period - first_period) / first_period * 100 if first_period > 0 else 0,
        "peak_month": str(monthly.loc[monthly["missing_rate"].idxmax(), "month"]),
        "peak_rate": monthly["missing_rate"].max(),
        "lowest_month": str(monthly.loc[monthly["missing_rate"].idxmin(), "month"]),
        "lowest_rate": monthly["missing_rate"].min(),
    }

    return trend


def get_temporal_summary(orders_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive temporal summary.

    Args:
        orders_df: Orders DataFrame

    Returns:
        Dictionary with temporal summary
    """
    monthly = analyze_monthly_trends(orders_df)
    daily = analyze_day_of_week_patterns(orders_df)
    hourly = analyze_hourly_patterns(orders_df)
    trend = analyze_trend_direction(orders_df)
    anomalies = detect_temporal_anomalies(orders_df)

    summary = {
        "date_range": {
            "start": str(orders_df["order_date"].min()),
            "end": str(orders_df["order_date"].max()),
            "total_months": len(monthly),
        },
        "trend": trend,
        "anomalies": {
            "total": sum(len(v) for v in anomalies.values()),
            "details": anomalies
        },
        "patterns": {
            "worst_day": daily.loc[daily["missing_rate"].idxmax(), "day_of_week"],
            "best_day": daily.loc[daily["missing_rate"].idxmin(), "day_of_week"],
            "worst_hour": int(hourly.loc[hourly["missing_rate"].idxmax(), "hour"]),
            "best_hour": int(hourly.loc[hourly["missing_rate"].idxmin(), "hour"]),
            "weekend_vs_weekday": {
                "weekend_rate": daily[daily["is_weekend"]]["missing_rate"].mean(),
                "weekday_rate": daily[~daily["is_weekend"]]["missing_rate"].mean(),
            }
        }
    }

    return summary

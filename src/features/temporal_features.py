"""
Temporal feature engineering for time-based analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, List


def create_temporal_features(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create temporal features from orders data.

    Features created:
    - hour: Hour of delivery
    - period: Morning/Afternoon/Evening/Night
    - day_of_week: Day name
    - day_of_week_num: Day number (0=Monday)
    - is_weekend: Boolean
    - week_of_year: Week number
    - month: Month number
    - month_name: Month name
    - quarter: Quarter number
    - is_month_start: First week of month
    - is_month_end: Last week of month

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with temporal features
    """
    df = orders_df.copy()

    # Ensure datetime
    df["order_date"] = pd.to_datetime(df["order_date"])

    # Extract hour from delivery_hour
    if "delivery_hour" in df.columns:
        df["hour"] = pd.to_datetime(
            df["delivery_hour"].astype(str), format="%H:%M:%S", errors="coerce"
        ).dt.hour

        # Delivery period
        df["period"] = pd.cut(
            df["hour"],
            bins=[-1, 6, 12, 18, 24],
            labels=["Night", "Morning", "Afternoon", "Evening"]
        )

    # Day features
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["day_of_week_num"] = df["order_date"].dt.dayofweek
    df["is_weekend"] = df["day_of_week_num"] >= 5

    # Week features
    df["week_of_year"] = df["order_date"].dt.isocalendar().week

    # Month features
    df["month"] = df["order_date"].dt.month
    df["month_name"] = df["order_date"].dt.month_name()
    df["day_of_month"] = df["order_date"].dt.day
    df["is_month_start"] = df["day_of_month"] <= 7
    df["is_month_end"] = df["day_of_month"] >= 24

    # Quarter
    df["quarter"] = df["order_date"].dt.quarter

    return df


def aggregate_by_time_period(
    orders_df: pd.DataFrame,
    period: str = "month"
) -> pd.DataFrame:
    """
    Aggregate orders by time period.

    Args:
        orders_df: Orders DataFrame with temporal features
        period: Aggregation period ('day', 'week', 'month', 'quarter')

    Returns:
        Aggregated DataFrame
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])

    period_map = {
        "day": "D",
        "week": "W",
        "month": "ME",
        "quarter": "QE"
    }

    freq = period_map.get(period, "ME")

    agg = df.groupby(pd.Grouper(key="order_date", freq=freq)).agg({
        "order_id": "count",
        "order_amount": "sum",
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    agg.columns = ["period", "total_orders", "total_revenue", "items_delivered", "items_missing"]

    # Calculate missing rate
    agg["total_items"] = agg["items_delivered"] + agg["items_missing"]
    agg["missing_rate"] = np.where(
        agg["total_items"] > 0,
        (agg["items_missing"] / agg["total_items"]) * 100,
        0
    )

    return agg


def get_hourly_patterns(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze patterns by hour of day.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with hourly patterns
    """
    df = orders_df.copy()

    # Extract hour
    df["hour"] = pd.to_datetime(
        df["delivery_hour"].astype(str), format="%H:%M:%S", errors="coerce"
    ).dt.hour

    hourly = df.groupby("hour").agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_amount": "mean",
    }).reset_index()

    hourly.columns = ["hour", "total_orders", "items_missing", "items_delivered", "avg_order_value"]

    hourly["total_items"] = hourly["items_delivered"] + hourly["items_missing"]
    hourly["missing_rate"] = np.where(
        hourly["total_items"] > 0,
        (hourly["items_missing"] / hourly["total_items"]) * 100,
        0
    )

    # Add period label
    hourly["period"] = pd.cut(
        hourly["hour"],
        bins=[-1, 6, 12, 18, 24],
        labels=["Night", "Morning", "Afternoon", "Evening"]
    )

    return hourly


def get_daily_patterns(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze patterns by day of week.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with daily patterns
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["day_num"] = df["order_date"].dt.dayofweek

    daily = df.groupby(["day_num", "day_of_week"]).agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_amount": ["sum", "mean"],
    }).reset_index()

    daily.columns = [
        "day_num", "day_of_week", "total_orders", "items_missing",
        "items_delivered", "total_revenue", "avg_order_value"
    ]

    daily["total_items"] = daily["items_delivered"] + daily["items_missing"]
    daily["missing_rate"] = np.where(
        daily["total_items"] > 0,
        (daily["items_missing"] / daily["total_items"]) * 100,
        0
    )

    daily["is_weekend"] = daily["day_num"] >= 5

    return daily.sort_values("day_num")


def get_monthly_trends(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze monthly trends.

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
        "items_missing": "sum",
        "items_delivered": "sum",
        "order_amount": ["sum", "mean"],
    }).reset_index()

    monthly.columns = [
        "month", "total_orders", "items_missing", "items_delivered",
        "total_revenue", "avg_order_value"
    ]

    monthly["total_items"] = monthly["items_delivered"] + monthly["items_missing"]
    monthly["missing_rate"] = np.where(
        monthly["total_items"] > 0,
        (monthly["items_missing"] / monthly["total_items"]) * 100,
        0
    )

    # Calculate month-over-month changes
    monthly["orders_mom_change"] = monthly["total_orders"].pct_change() * 100
    monthly["missing_rate_mom_change"] = monthly["missing_rate"].diff()

    return monthly


def detect_temporal_anomalies(
    orders_df: pd.DataFrame,
    threshold_std: float = 2.0
) -> Dict[str, List]:
    """
    Detect temporal anomalies in missing rates.

    Args:
        orders_df: Orders DataFrame
        threshold_std: Number of standard deviations for anomaly

    Returns:
        Dictionary with anomalous periods
    """
    anomalies = {
        "high_risk_hours": [],
        "high_risk_days": [],
        "high_risk_months": [],
    }

    # Hourly anomalies
    hourly = get_hourly_patterns(orders_df)
    mean_rate = hourly["missing_rate"].mean()
    std_rate = hourly["missing_rate"].std()
    threshold = mean_rate + threshold_std * std_rate

    anomalies["high_risk_hours"] = hourly[hourly["missing_rate"] > threshold]["hour"].tolist()

    # Daily anomalies
    daily = get_daily_patterns(orders_df)
    mean_rate = daily["missing_rate"].mean()
    std_rate = daily["missing_rate"].std()
    threshold = mean_rate + threshold_std * std_rate

    anomalies["high_risk_days"] = daily[daily["missing_rate"] > threshold]["day_of_week"].tolist()

    # Monthly anomalies
    monthly = get_monthly_trends(orders_df)
    mean_rate = monthly["missing_rate"].mean()
    std_rate = monthly["missing_rate"].std()
    threshold = mean_rate + threshold_std * std_rate

    anomalies["high_risk_months"] = monthly[monthly["missing_rate"] > threshold]["month"].astype(str).tolist()

    return anomalies

"""
Feature engineering for orders.
"""
import pandas as pd
import numpy as np
from typing import Optional


def create_order_features(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create features from orders data.

    Features created:
    - missing_rate: Percentage of items missing
    - is_high_value: Order above 75th percentile
    - delivery_period: Morning/Afternoon/Evening/Night
    - day_of_week: Day name
    - is_weekend: Boolean
    - month: Month number
    - order_size: Small/Medium/Large based on total items

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with new features
    """
    df = orders_df.copy()

    # Total items
    df["total_items"] = df["items_delivered"] + df["items_missing"]

    # Missing rate
    df["missing_rate"] = np.where(
        df["total_items"] > 0,
        (df["items_missing"] / df["total_items"]) * 100,
        0
    )

    # High value order (above 75th percentile)
    threshold = df["order_amount"].quantile(0.75)
    df["is_high_value"] = df["order_amount"] > threshold

    # Delivery period
    df["delivery_hour_int"] = pd.to_datetime(
        df["delivery_hour"].astype(str), format="%H:%M:%S", errors="coerce"
    ).dt.hour

    df["delivery_period"] = pd.cut(
        df["delivery_hour_int"],
        bins=[-1, 6, 12, 18, 24],
        labels=["Night", "Morning", "Afternoon", "Evening"]
    )

    # Date features
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["day_of_week"] = df["order_date"].dt.day_name()
    df["is_weekend"] = df["order_date"].dt.dayofweek >= 5
    df["month"] = df["order_date"].dt.month
    df["week_of_year"] = df["order_date"].dt.isocalendar().week

    # Order size category
    df["order_size"] = pd.cut(
        df["total_items"],
        bins=[-1, 5, 10, float("inf")],
        labels=["Small", "Medium", "Large"]
    )

    # Has missing items flag
    df["has_missing"] = df["items_missing"] > 0

    return df


def create_order_aggregations(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create aggregated statistics from orders.

    Args:
        orders_df: Orders DataFrame with features

    Returns:
        DataFrame with global statistics
    """
    stats = {
        "total_orders": len(orders_df),
        "total_revenue": orders_df["order_amount"].sum(),
        "avg_order_value": orders_df["order_amount"].mean(),
        "total_items_delivered": orders_df["items_delivered"].sum(),
        "total_items_missing": orders_df["items_missing"].sum(),
        "overall_missing_rate": (
            orders_df["items_missing"].sum() /
            (orders_df["items_delivered"].sum() + orders_df["items_missing"].sum()) * 100
        ),
        "orders_with_missing": (orders_df["items_missing"] > 0).sum(),
        "pct_orders_with_missing": (orders_df["items_missing"] > 0).mean() * 100,
    }

    return pd.DataFrame([stats])


def get_high_risk_orders(
    orders_df: pd.DataFrame,
    missing_rate_threshold: float = 50.0,
    value_threshold: Optional[float] = None
) -> pd.DataFrame:
    """
    Identify high-risk orders based on missing rate and value.

    Args:
        orders_df: Orders DataFrame with features
        missing_rate_threshold: Minimum missing rate to flag
        value_threshold: Minimum order value to flag (uses median if None)

    Returns:
        DataFrame with high-risk orders
    """
    df = orders_df.copy()

    if "missing_rate" not in df.columns:
        df = create_order_features(df)

    if value_threshold is None:
        value_threshold = df["order_amount"].median()

    high_risk = df[
        (df["missing_rate"] >= missing_rate_threshold) |
        ((df["has_missing"]) & (df["order_amount"] >= value_threshold))
    ]

    return high_risk.sort_values("missing_rate", ascending=False)

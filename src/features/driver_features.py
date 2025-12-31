"""
Feature engineering for drivers.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def create_driver_features(
    drivers_df: pd.DataFrame,
    orders_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create features for drivers based on their delivery history.

    Features created:
    - total_orders: Number of orders delivered
    - total_items_delivered: Total items delivered
    - total_items_missing: Total items reported missing
    - missing_rate: Percentage of items missing
    - orders_with_missing: Number of orders with missing items
    - pct_orders_with_missing: Percentage of orders with issues
    - avg_order_value: Average order value delivered
    - total_revenue: Total revenue from deliveries
    - age_group: Age category
    - experience_level: Based on trips

    Args:
        drivers_df: Drivers DataFrame
        orders_df: Orders DataFrame

    Returns:
        DataFrame with driver features
    """
    # Aggregate orders by driver
    driver_stats = orders_df.groupby("driver_id").agg({
        "order_id": "count",
        "items_delivered": "sum",
        "items_missing": "sum",
        "order_amount": ["sum", "mean"],
    }).reset_index()

    # Flatten column names
    driver_stats.columns = [
        "driver_id", "total_orders", "total_items_delivered",
        "total_items_missing", "total_revenue", "avg_order_value"
    ]

    # Calculate missing rate
    driver_stats["missing_rate"] = np.where(
        (driver_stats["total_items_delivered"] + driver_stats["total_items_missing"]) > 0,
        (driver_stats["total_items_missing"] /
         (driver_stats["total_items_delivered"] + driver_stats["total_items_missing"])) * 100,
        0
    )

    # Count orders with missing items
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("driver_id").size()
    driver_stats["orders_with_missing"] = driver_stats["driver_id"].map(orders_with_missing).fillna(0).astype(int)
    driver_stats["pct_orders_with_missing"] = (
        driver_stats["orders_with_missing"] / driver_stats["total_orders"] * 100
    )

    # Merge with driver info
    df = drivers_df.merge(driver_stats, on="driver_id", how="left")

    # Fill NaN for drivers with no orders
    numeric_cols = [
        "total_orders", "total_items_delivered", "total_items_missing",
        "total_revenue", "avg_order_value", "missing_rate",
        "orders_with_missing", "pct_orders_with_missing"
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Age group
    df["age_group"] = pd.cut(
        df["age"],
        bins=[0, 25, 35, 45, 55, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "55+"]
    )

    # Experience level based on trips
    df["experience_level"] = pd.cut(
        df["trips"],
        bins=[-1, 25, 50, 100, float("inf")],
        labels=["Novice", "Intermediate", "Experienced", "Expert"]
    )

    return df


def get_driver_risk_scores(driver_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate risk scores for drivers.

    Risk score is based on:
    - Missing rate (higher = more risk)
    - Percentage of orders with missing items
    - Total items missing (volume)

    Args:
        driver_features_df: DataFrame with driver features

    Returns:
        DataFrame with risk scores
    """
    df = driver_features_df.copy()

    # Normalize features to 0-1 scale
    def min_max_scale(series):
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series([0.5] * len(series))
        return (series - min_val) / (max_val - min_val)

    # Calculate component scores
    df["missing_rate_score"] = min_max_scale(df["missing_rate"])
    df["pct_orders_score"] = min_max_scale(df["pct_orders_with_missing"])
    df["volume_score"] = min_max_scale(df["total_items_missing"])

    # Weighted risk score
    df["risk_score"] = (
        df["missing_rate_score"] * 0.4 +
        df["pct_orders_score"] * 0.35 +
        df["volume_score"] * 0.25
    ) * 100

    # Risk category
    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"]
    )

    return df


def get_suspicious_drivers(
    driver_features_df: pd.DataFrame,
    missing_rate_threshold: float = 20.0,
    min_orders: int = 5
) -> pd.DataFrame:
    """
    Identify suspicious drivers based on anomaly thresholds.

    Args:
        driver_features_df: DataFrame with driver features
        missing_rate_threshold: Minimum missing rate to flag
        min_orders: Minimum orders to consider (avoid flagging new drivers)

    Returns:
        DataFrame with suspicious drivers
    """
    df = driver_features_df.copy()

    # Calculate statistics for thresholds
    mean_rate = df["missing_rate"].mean()
    std_rate = df["missing_rate"].std()

    # Flag drivers above threshold or 2 standard deviations above mean
    suspicious = df[
        (df["total_orders"] >= min_orders) &
        (
            (df["missing_rate"] >= missing_rate_threshold) |
            (df["missing_rate"] > mean_rate + 2 * std_rate)
        )
    ]

    return suspicious.sort_values("missing_rate", ascending=False)


def compare_driver_performance(
    driver_features_df: pd.DataFrame
) -> Tuple[pd.DataFrame, dict]:
    """
    Compare driver performance and identify outliers.

    Returns:
        Tuple of (comparison DataFrame, statistics dict)
    """
    df = driver_features_df.copy()

    stats = {
        "avg_missing_rate": df["missing_rate"].mean(),
        "median_missing_rate": df["missing_rate"].median(),
        "std_missing_rate": df["missing_rate"].std(),
        "q1_missing_rate": df["missing_rate"].quantile(0.25),
        "q3_missing_rate": df["missing_rate"].quantile(0.75),
        "total_drivers": len(df),
        "drivers_above_avg": (df["missing_rate"] > df["missing_rate"].mean()).sum(),
    }

    # Add comparison columns
    df["vs_avg"] = df["missing_rate"] - stats["avg_missing_rate"]
    df["is_above_avg"] = df["missing_rate"] > stats["avg_missing_rate"]
    df["is_outlier"] = df["missing_rate"] > (stats["avg_missing_rate"] + 2 * stats["std_missing_rate"])

    return df, stats

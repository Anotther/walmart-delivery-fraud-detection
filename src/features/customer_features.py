"""
Feature engineering for customers.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def create_customer_features(
    customers_df: pd.DataFrame,
    orders_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create features for customers based on their order history.

    Features created:
    - total_orders: Number of orders placed
    - total_spent: Total amount spent
    - avg_order_value: Average order value
    - total_items_ordered: Total items ordered
    - total_items_missing: Total items reported missing
    - missing_rate: Percentage of items missing
    - orders_with_missing: Number of orders with issues
    - pct_orders_with_missing: Percentage of orders with issues
    - age_group: Age category
    - customer_segment: Based on spending

    Args:
        customers_df: Customers DataFrame
        orders_df: Orders DataFrame

    Returns:
        DataFrame with customer features
    """
    # Aggregate orders by customer
    customer_stats = orders_df.groupby("customer_id").agg({
        "order_id": "count",
        "order_amount": ["sum", "mean"],
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    # Flatten column names
    customer_stats.columns = [
        "customer_id", "total_orders", "total_spent", "avg_order_value",
        "total_items_delivered", "total_items_missing"
    ]

    # Calculate total items and missing rate
    customer_stats["total_items_ordered"] = (
        customer_stats["total_items_delivered"] + customer_stats["total_items_missing"]
    )

    customer_stats["missing_rate"] = np.where(
        customer_stats["total_items_ordered"] > 0,
        (customer_stats["total_items_missing"] / customer_stats["total_items_ordered"]) * 100,
        0
    )

    # Count orders with missing items
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("customer_id").size()
    customer_stats["orders_with_missing"] = (
        customer_stats["customer_id"].map(orders_with_missing).fillna(0).astype(int)
    )
    customer_stats["pct_orders_with_missing"] = (
        customer_stats["orders_with_missing"] / customer_stats["total_orders"] * 100
    )

    # Merge with customer info
    df = customers_df.merge(customer_stats, on="customer_id", how="left")

    # Fill NaN for customers with no orders
    numeric_cols = [
        "total_orders", "total_spent", "avg_order_value",
        "total_items_delivered", "total_items_missing", "total_items_ordered",
        "missing_rate", "orders_with_missing", "pct_orders_with_missing"
    ]
    df[numeric_cols] = df[numeric_cols].fillna(0)

    # Age group
    df["age_group"] = pd.cut(
        df["customer_age"],
        bins=[0, 25, 35, 45, 55, 65, 100],
        labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
    )

    # Customer segment based on spending
    spending_q = df["total_spent"].quantile([0.25, 0.5, 0.75])
    df["customer_segment"] = pd.cut(
        df["total_spent"],
        bins=[-1, spending_q[0.25], spending_q[0.5], spending_q[0.75], float("inf")],
        labels=["Low Value", "Medium Value", "High Value", "VIP"]
    )

    return df


def get_customer_risk_scores(customer_features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate risk scores for customers.

    Risk indicates potential fraud by customer claiming missing items.

    Args:
        customer_features_df: DataFrame with customer features

    Returns:
        DataFrame with risk scores
    """
    df = customer_features_df.copy()

    # Normalize features
    def min_max_scale(series):
        min_val = series.min()
        max_val = series.max()
        if max_val - min_val == 0:
            return pd.Series([0.5] * len(series))
        return (series - min_val) / (max_val - min_val)

    # Calculate component scores
    df["missing_rate_score"] = min_max_scale(df["missing_rate"])
    df["pct_orders_score"] = min_max_scale(df["pct_orders_with_missing"])
    df["frequency_score"] = min_max_scale(df["orders_with_missing"])

    # Weighted risk score
    df["risk_score"] = (
        df["missing_rate_score"] * 0.4 +
        df["pct_orders_score"] * 0.35 +
        df["frequency_score"] * 0.25
    ) * 100

    # Risk category
    df["risk_category"] = pd.cut(
        df["risk_score"],
        bins=[-1, 25, 50, 75, 100],
        labels=["Low", "Medium", "High", "Critical"]
    )

    return df


def get_suspicious_customers(
    customer_features_df: pd.DataFrame,
    missing_rate_threshold: float = 30.0,
    min_orders: int = 3
) -> pd.DataFrame:
    """
    Identify suspicious customers based on anomaly thresholds.

    Args:
        customer_features_df: DataFrame with customer features
        missing_rate_threshold: Minimum missing rate to flag
        min_orders: Minimum orders to consider

    Returns:
        DataFrame with suspicious customers
    """
    df = customer_features_df.copy()

    # Calculate statistics
    mean_rate = df["missing_rate"].mean()
    std_rate = df["missing_rate"].std()

    # Flag customers above threshold or outliers
    suspicious = df[
        (df["total_orders"] >= min_orders) &
        (
            (df["missing_rate"] >= missing_rate_threshold) |
            (df["missing_rate"] > mean_rate + 2 * std_rate)
        )
    ]

    return suspicious.sort_values("missing_rate", ascending=False)


def analyze_customer_patterns(
    customer_features_df: pd.DataFrame,
    orders_df: pd.DataFrame
) -> dict:
    """
    Analyze customer behavior patterns.

    Args:
        customer_features_df: DataFrame with customer features
        orders_df: Orders DataFrame

    Returns:
        Dictionary with pattern analysis
    """
    df = customer_features_df.copy()

    patterns = {
        "total_customers": len(df),
        "customers_with_issues": (df["orders_with_missing"] > 0).sum(),
        "pct_customers_with_issues": (df["orders_with_missing"] > 0).mean() * 100,
        "avg_missing_rate": df["missing_rate"].mean(),
        "median_missing_rate": df["missing_rate"].median(),
        "repeat_offenders": (df["orders_with_missing"] > 1).sum(),
    }

    # Age group analysis
    age_analysis = df.groupby("age_group").agg({
        "missing_rate": "mean",
        "orders_with_missing": "sum",
        "customer_id": "count"
    }).rename(columns={"customer_id": "customer_count"})

    patterns["age_group_analysis"] = age_analysis.to_dict()

    # Segment analysis
    segment_analysis = df.groupby("customer_segment").agg({
        "missing_rate": "mean",
        "total_spent": "sum",
        "customer_id": "count"
    }).rename(columns={"customer_id": "customer_count"})

    patterns["segment_analysis"] = segment_analysis.to_dict()

    return patterns

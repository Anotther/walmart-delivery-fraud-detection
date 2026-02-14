"""
Geographic analysis for regional fraud patterns.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple

from src.config.risk_thresholds import RiskThresholds


def analyze_regional_performance(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze performance metrics by region.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with regional performance metrics
    """
    regional = orders_df.groupby("region").agg({
        "order_id": "count",
        "order_amount": ["sum", "mean"],
        "items_delivered": "sum",
        "items_missing": "sum",
        "driver_id": "nunique",
        "customer_id": "nunique",
    }).reset_index()

    regional.columns = [
        "region", "total_orders", "total_revenue", "avg_order_value",
        "items_delivered", "items_missing", "unique_drivers", "unique_customers"
    ]

    regional["total_items"] = regional["items_delivered"] + regional["items_missing"]
    regional["missing_rate"] = np.where(
        regional["total_items"] > 0,
        regional["items_missing"] / regional["total_items"] * 100,
        0
    )

    # Orders with missing items
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("region").size()
    regional["orders_with_missing"] = regional["region"].map(orders_with_missing).fillna(0).astype(int)
    regional["pct_orders_with_missing"] = (
        regional["orders_with_missing"] / regional["total_orders"] * 100
    )

    # Orders per driver ratio
    regional["orders_per_driver"] = regional["total_orders"] / regional["unique_drivers"]

    # Revenue per customer
    regional["revenue_per_customer"] = regional["total_revenue"] / regional["unique_customers"]

    return regional.sort_values("missing_rate", ascending=False)


def compare_regions(
    orders_df: pd.DataFrame,
    metric: str = "missing_rate"
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Compare regions against each other and the average.

    Args:
        orders_df: Orders DataFrame
        metric: Metric to compare

    Returns:
        Tuple of (comparison DataFrame, statistics dict)
    """
    regional = analyze_regional_performance(orders_df)

    avg_value = regional[metric].mean()
    std_value = regional[metric].std()

    regional["vs_avg"] = regional[metric] - avg_value
    regional["vs_avg_pct"] = (regional[metric] - avg_value) / avg_value * 100
    regional["z_score"] = (regional[metric] - avg_value) / std_value if std_value > 0 else 0
    regional["is_above_avg"] = regional[metric] > avg_value
    regional["is_outlier"] = abs(regional["z_score"]) > 2

    stats = {
        "metric": metric,
        "average": avg_value,
        "std": std_value,
        "min": regional[metric].min(),
        "max": regional[metric].max(),
        "best_region": regional.loc[regional[metric].idxmin(), "region"],
        "worst_region": regional.loc[regional[metric].idxmax(), "region"],
        "outliers": regional[regional["is_outlier"]]["region"].tolist(),
    }

    return regional, stats


def analyze_regional_drivers(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Analyze driver performance by region.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame

    Returns:
        DataFrame with driver-region analysis
    """
    # Get orders with driver and region info
    driver_region = orders_df.groupby(["region", "driver_id"]).agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
    }).reset_index()

    driver_region.columns = [
        "region", "driver_id", "orders_in_region",
        "items_missing", "items_delivered"
    ]

    driver_region["total_items"] = driver_region["items_delivered"] + driver_region["items_missing"]
    driver_region["missing_rate"] = np.where(
        driver_region["total_items"] > 0,
        driver_region["items_missing"] / driver_region["total_items"] * 100,
        0
    )

    # Merge with driver info
    driver_region = driver_region.merge(
        drivers_df[["driver_id", "driver_name", "age", "trips"]],
        on="driver_id",
        how="left"
    )

    return driver_region


def identify_regional_hotspots(
    orders_df: pd.DataFrame,
    threshold_pct: float = None
) -> Dict[str, List[str]]:
    """
    Identify regions with high fraud indicators.

    Args:
        orders_df: Orders DataFrame
        threshold_pct: Percentile threshold for hotspot (default: RiskThresholds.GEOGRAPHIC_RANK)

    Returns:
        Dictionary with hotspot categories
    """
    if threshold_pct is None:
        threshold_pct = RiskThresholds.GEOGRAPHIC_RANK
    regional = analyze_regional_performance(orders_df)

    hotspots = {
        "high_missing_rate": [],
        "high_volume_missing": [],
        "low_driver_coverage": [],
    }

    # High missing rate regions
    threshold = regional["missing_rate"].quantile(threshold_pct / 100)
    hotspots["high_missing_rate"] = regional[
        regional["missing_rate"] >= threshold
    ]["region"].tolist()

    # High volume of missing items
    threshold = regional["items_missing"].quantile(threshold_pct / 100)
    hotspots["high_volume_missing"] = regional[
        regional["items_missing"] >= threshold
    ]["region"].tolist()

    # Low driver coverage (many orders per driver)
    threshold = regional["orders_per_driver"].quantile(threshold_pct / 100)
    hotspots["low_driver_coverage"] = regional[
        regional["orders_per_driver"] >= threshold
    ]["region"].tolist()

    return hotspots


def analyze_regional_time_patterns(
    orders_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Analyze time patterns within each region.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with regional time patterns
    """
    df = orders_df.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["month"] = df["order_date"].dt.month
    df["day_of_week"] = df["order_date"].dt.dayofweek

    # Extract hour
    df["hour"] = pd.to_datetime(
        df["delivery_hour"].astype(str), format="%H:%M:%S", errors="coerce"
    ).dt.hour

    # Monthly patterns by region
    monthly_regional = df.groupby(["region", "month"]).agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
    }).reset_index()

    monthly_regional.columns = [
        "region", "month", "orders", "items_missing", "items_delivered"
    ]
    monthly_regional["total_items"] = monthly_regional["items_delivered"] + monthly_regional["items_missing"]
    monthly_regional["missing_rate"] = np.where(
        monthly_regional["total_items"] > 0,
        monthly_regional["items_missing"] / monthly_regional["total_items"] * 100,
        0
    )

    return monthly_regional


def get_regional_summary(orders_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a comprehensive regional summary.

    Args:
        orders_df: Orders DataFrame

    Returns:
        Dictionary with regional summary
    """
    regional = analyze_regional_performance(orders_df)

    summary = {
        "total_regions": len(regional),
        "overview": regional[
            ["region", "total_orders", "missing_rate", "pct_orders_with_missing"]
        ].to_dict(orient="records"),
        "best_performing": regional.nsmallest(3, "missing_rate")[
            ["region", "missing_rate", "total_orders"]
        ].to_dict(orient="records"),
        "worst_performing": regional.nlargest(3, "missing_rate")[
            ["region", "missing_rate", "total_orders"]
        ].to_dict(orient="records"),
        "statistics": {
            "avg_missing_rate": regional["missing_rate"].mean(),
            "std_missing_rate": regional["missing_rate"].std(),
            "total_orders": regional["total_orders"].sum(),
            "total_missing_items": regional["items_missing"].sum(),
        }
    }

    return summary

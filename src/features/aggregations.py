"""
Combined aggregations and feature combinations.
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple

from src.features.order_features import create_order_features
from src.features.driver_features import create_driver_features
from src.features.customer_features import create_customer_features
from src.features.temporal_features import create_temporal_features


def create_all_features(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame,
    missing_items_df: pd.DataFrame
) -> Dict[str, pd.DataFrame]:
    """
    Create all features for the dataset.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        customers_df: Customers DataFrame
        products_df: Products DataFrame
        missing_items_df: Missing items DataFrame

    Returns:
        Dictionary with all feature DataFrames
    """
    # Order features with temporal
    orders_features = create_order_features(orders_df)
    orders_features = create_temporal_features(orders_features)

    # Driver features
    driver_features = create_driver_features(drivers_df, orders_df)

    # Customer features
    customer_features = create_customer_features(customers_df, orders_df)

    # Product features
    product_features = create_product_features(products_df, missing_items_df)

    return {
        "orders": orders_features,
        "drivers": driver_features,
        "customers": customer_features,
        "products": product_features,
    }


def create_product_features(
    products_df: pd.DataFrame,
    missing_items_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create features for products based on missing item reports.

    Args:
        products_df: Products DataFrame
        missing_items_df: Missing items DataFrame

    Returns:
        DataFrame with product features
    """
    df = products_df.copy()

    # Count how many times each product was reported missing
    missing_counts = {}

    for col in ["product_id_1", "product_id_2", "product_id_3"]:
        if col in missing_items_df.columns:
            counts = missing_items_df[col].value_counts()
            for pid, count in counts.items():
                if pd.notna(pid):
                    missing_counts[pid] = missing_counts.get(pid, 0) + count

    df["times_reported_missing"] = df["product_id"].map(missing_counts).fillna(0).astype(int)

    # Price category
    df["price_category"] = pd.cut(
        df["price"],
        bins=[-1, 10, 25, 50, 100, float("inf")],
        labels=["Very Low", "Low", "Medium", "High", "Premium"]
    )

    # Missing rate per category
    category_missing = df.groupby("category")["times_reported_missing"].sum()
    df["category_total_missing"] = df["category"].map(category_missing)

    return df


def create_regional_features(orders_df: pd.DataFrame) -> pd.DataFrame:
    """
    Create features aggregated by region.

    Args:
        orders_df: Orders DataFrame

    Returns:
        DataFrame with regional features
    """
    regional = orders_df.groupby("region").agg({
        "order_id": "count",
        "order_amount": ["sum", "mean"],
        "items_delivered": "sum",
        "items_missing": "sum",
    }).reset_index()

    regional.columns = [
        "region", "total_orders", "total_revenue", "avg_order_value",
        "items_delivered", "items_missing"
    ]

    regional["total_items"] = regional["items_delivered"] + regional["items_missing"]
    regional["missing_rate"] = np.where(
        regional["total_items"] > 0,
        (regional["items_missing"] / regional["total_items"]) * 100,
        0
    )

    # Count orders with issues
    orders_with_missing = orders_df[orders_df["items_missing"] > 0].groupby("region").size()
    regional["orders_with_missing"] = regional["region"].map(orders_with_missing).fillna(0).astype(int)
    regional["pct_orders_with_missing"] = (
        regional["orders_with_missing"] / regional["total_orders"] * 100
    )

    # Unique drivers and customers per region
    unique_drivers = orders_df.groupby("region")["driver_id"].nunique()
    unique_customers = orders_df.groupby("region")["customer_id"].nunique()

    regional["unique_drivers"] = regional["region"].map(unique_drivers)
    regional["unique_customers"] = regional["region"].map(unique_customers)

    return regional


def create_driver_customer_matrix(
    orders_df: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create driver-customer interaction matrix.

    Useful for detecting collusion patterns.

    Args:
        orders_df: Orders DataFrame

    Returns:
        Tuple of (interaction matrix, suspicious pairs DataFrame)
    """
    # Count interactions between drivers and customers
    interactions = orders_df.groupby(["driver_id", "customer_id"]).agg({
        "order_id": "count",
        "items_missing": "sum",
        "items_delivered": "sum",
    }).reset_index()

    interactions.columns = ["driver_id", "customer_id", "interactions", "items_missing", "items_delivered"]

    interactions["total_items"] = interactions["items_delivered"] + interactions["items_missing"]
    interactions["missing_rate"] = np.where(
        interactions["total_items"] > 0,
        (interactions["items_missing"] / interactions["total_items"]) * 100,
        0
    )

    # Find suspicious pairs (high interaction + high missing rate)
    avg_interactions = interactions["interactions"].mean()
    avg_missing_rate = interactions["missing_rate"].mean()

    suspicious = interactions[
        (interactions["interactions"] > avg_interactions) &
        (interactions["missing_rate"] > avg_missing_rate * 1.5)
    ].sort_values("missing_rate", ascending=False)

    return interactions, suspicious


def get_overall_statistics(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    customers_df: pd.DataFrame
) -> Dict:
    """
    Calculate overall statistics for the dataset.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        customers_df: Customers DataFrame

    Returns:
        Dictionary with overall statistics
    """
    total_items = orders_df["items_delivered"].sum() + orders_df["items_missing"].sum()

    stats = {
        # Orders
        "total_orders": len(orders_df),
        "total_revenue": orders_df["order_amount"].sum(),
        "avg_order_value": orders_df["order_amount"].mean(),

        # Items
        "total_items_delivered": orders_df["items_delivered"].sum(),
        "total_items_missing": orders_df["items_missing"].sum(),
        "overall_missing_rate": (orders_df["items_missing"].sum() / total_items * 100) if total_items > 0 else 0,

        # Orders with issues
        "orders_with_missing": (orders_df["items_missing"] > 0).sum(),
        "pct_orders_with_missing": (orders_df["items_missing"] > 0).mean() * 100,

        # Drivers
        "total_drivers": len(drivers_df),
        "active_drivers": orders_df["driver_id"].nunique(),

        # Customers
        "total_customers": len(customers_df),
        "active_customers": orders_df["customer_id"].nunique(),

        # Regions
        "total_regions": orders_df["region"].nunique(),

        # Time range
        "date_range_start": orders_df["order_date"].min(),
        "date_range_end": orders_df["order_date"].max(),
    }

    return stats


def create_fraud_detection_dataset(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    customers_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Create a consolidated dataset for fraud detection modeling.

    Joins all features into a single DataFrame for ML.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        customers_df: Customers DataFrame

    Returns:
        Consolidated DataFrame for modeling
    """
    # Create features
    orders_feat = create_order_features(orders_df)
    orders_feat = create_temporal_features(orders_feat)

    driver_feat = create_driver_features(drivers_df, orders_df)
    customer_feat = create_customer_features(customers_df, orders_df)

    # Select driver features to join
    driver_cols = [
        "driver_id", "age", "trips", "missing_rate", "total_orders",
        "pct_orders_with_missing", "experience_level"
    ]
    driver_subset = driver_feat[driver_cols].rename(columns={
        "missing_rate": "driver_missing_rate",
        "total_orders": "driver_total_orders",
        "pct_orders_with_missing": "driver_pct_orders_with_missing",
        "age": "driver_age",
    })

    # Select customer features to join
    customer_cols = [
        "customer_id", "customer_age", "total_orders", "missing_rate",
        "pct_orders_with_missing", "customer_segment"
    ]
    customer_subset = customer_feat[customer_cols].rename(columns={
        "missing_rate": "customer_missing_rate",
        "total_orders": "customer_total_orders",
        "pct_orders_with_missing": "customer_pct_orders_with_missing",
    })

    # Join all features
    df = orders_feat.merge(driver_subset, on="driver_id", how="left")
    df = df.merge(customer_subset, on="customer_id", how="left")

    # Create target variable
    df["is_fraud_candidate"] = df["has_missing"].astype(int)

    return df

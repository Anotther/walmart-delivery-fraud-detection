"""
Descriptive statistics and basic analysis.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional


def describe_dataset(df: pd.DataFrame, name: str = "Dataset") -> Dict[str, Any]:
    """
    Generate comprehensive descriptive statistics for a DataFrame.

    Args:
        df: DataFrame to analyze
        name: Name of the dataset

    Returns:
        Dictionary with statistics
    """
    stats = {
        "name": name,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        "column_types": df.dtypes.value_counts().to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "missing_pct": (df.isnull().sum() / len(df) * 100).to_dict(),
    }

    # Numeric columns statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if numeric_cols:
        stats["numeric_stats"] = df[numeric_cols].describe().to_dict()

    return stats


def describe_orders(orders_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate descriptive statistics specific to orders data.

    Args:
        orders_df: Orders DataFrame

    Returns:
        Dictionary with order-specific statistics
    """
    df = orders_df.copy()

    stats = {
        "total_orders": len(df),
        "date_range": {
            "start": str(df["order_date"].min()),
            "end": str(df["order_date"].max()),
        },
        "order_amount": {
            "total": df["order_amount"].sum(),
            "mean": df["order_amount"].mean(),
            "median": df["order_amount"].median(),
            "std": df["order_amount"].std(),
            "min": df["order_amount"].min(),
            "max": df["order_amount"].max(),
        },
        "items_delivered": {
            "total": df["items_delivered"].sum(),
            "mean": df["items_delivered"].mean(),
            "median": df["items_delivered"].median(),
        },
        "items_missing": {
            "total": df["items_missing"].sum(),
            "mean": df["items_missing"].mean(),
            "median": df["items_missing"].median(),
            "max": df["items_missing"].max(),
        },
        "regions": df["region"].value_counts().to_dict(),
        "unique_drivers": df["driver_id"].nunique(),
        "unique_customers": df["customer_id"].nunique(),
    }

    # Missing rate
    total_items = df["items_delivered"].sum() + df["items_missing"].sum()
    stats["missing_rate_pct"] = (df["items_missing"].sum() / total_items * 100) if total_items > 0 else 0

    # Orders with missing items
    orders_with_missing = (df["items_missing"] > 0).sum()
    stats["orders_with_missing"] = orders_with_missing
    stats["pct_orders_with_missing"] = orders_with_missing / len(df) * 100

    return stats


def describe_drivers(drivers_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate descriptive statistics for drivers data.

    Args:
        drivers_df: Drivers DataFrame

    Returns:
        Dictionary with driver statistics
    """
    df = drivers_df.copy()

    stats = {
        "total_drivers": len(df),
        "age": {
            "mean": df["age"].mean(),
            "median": df["age"].median(),
            "min": df["age"].min(),
            "max": df["age"].max(),
            "std": df["age"].std(),
        },
        "trips": {
            "total": df["trips"].sum(),
            "mean": df["trips"].mean(),
            "median": df["trips"].median(),
            "min": df["trips"].min(),
            "max": df["trips"].max(),
        },
        "age_distribution": pd.cut(
            df["age"],
            bins=[0, 25, 35, 45, 55, 100],
            labels=["18-25", "26-35", "36-45", "46-55", "55+"]
        ).value_counts().to_dict(),
    }

    return stats


def describe_customers(customers_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate descriptive statistics for customers data.

    Args:
        customers_df: Customers DataFrame

    Returns:
        Dictionary with customer statistics
    """
    df = customers_df.copy()

    stats = {
        "total_customers": len(df),
        "age": {
            "mean": df["customer_age"].mean(),
            "median": df["customer_age"].median(),
            "min": df["customer_age"].min(),
            "max": df["customer_age"].max(),
            "std": df["customer_age"].std(),
        },
        "age_distribution": pd.cut(
            df["customer_age"],
            bins=[0, 25, 35, 45, 55, 65, 100],
            labels=["18-25", "26-35", "36-45", "46-55", "56-65", "65+"]
        ).value_counts().to_dict(),
    }

    return stats


def describe_products(products_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate descriptive statistics for products data.

    Args:
        products_df: Products DataFrame

    Returns:
        Dictionary with product statistics
    """
    df = products_df.copy()

    stats = {
        "total_products": len(df),
        "categories": df["category"].nunique(),
        "category_counts": df["category"].value_counts().to_dict(),
        "price": {
            "mean": df["price"].mean(),
            "median": df["price"].median(),
            "min": df["price"].min(),
            "max": df["price"].max(),
            "std": df["price"].std(),
        },
        "price_by_category": df.groupby("category")["price"].agg(["mean", "median", "min", "max"]).to_dict(),
    }

    return stats


def calculate_correlations(
    df: pd.DataFrame,
    numeric_only: bool = True
) -> pd.DataFrame:
    """
    Calculate correlation matrix for numeric columns.

    Args:
        df: DataFrame to analyze
        numeric_only: Only include numeric columns

    Returns:
        Correlation matrix DataFrame
    """
    if numeric_only:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return df[numeric_cols].corr()
    return df.corr()


def identify_outliers(
    df: pd.DataFrame,
    column: str,
    method: str = "iqr",
    threshold: float = 1.5
) -> pd.DataFrame:
    """
    Identify outliers in a column using specified method.

    Args:
        df: DataFrame to analyze
        column: Column to check for outliers
        method: 'iqr' or 'zscore'
        threshold: IQR multiplier or z-score threshold

    Returns:
        DataFrame with outlier rows
    """
    if method == "iqr":
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - threshold * iqr
        upper = q3 + threshold * iqr
        outliers = df[(df[column] < lower) | (df[column] > upper)]
    elif method == "zscore":
        mean = df[column].mean()
        std = df[column].std()
        z_scores = np.abs((df[column] - mean) / std)
        outliers = df[z_scores > threshold]
    else:
        raise ValueError(f"Unknown method: {method}")

    return outliers


def generate_summary_report(
    orders_df: pd.DataFrame,
    drivers_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    products_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    Generate a comprehensive summary report of all datasets.

    Args:
        orders_df: Orders DataFrame
        drivers_df: Drivers DataFrame
        customers_df: Customers DataFrame
        products_df: Products DataFrame

    Returns:
        Dictionary with complete summary
    """
    return {
        "orders": describe_orders(orders_df),
        "drivers": describe_drivers(drivers_df),
        "customers": describe_customers(customers_df),
        "products": describe_products(products_df),
    }

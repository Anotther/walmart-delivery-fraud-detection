"""
Data transformers for cleaning and transforming data.
"""
import pandas as pd
import numpy as np
from typing import Tuple


def parse_currency(value: str) -> float:
    """
    Parse currency string to float.

    Args:
        value: Currency string like "$1,234.56"

    Returns:
        Float value
    """
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float)):
        return float(value)
    # Remove $ and commas
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform orders DataFrame.

    Transformations:
    - Parse date column
    - Parse order_amount currency
    - Parse delivery_hour to time
    - Ensure integer columns

    Args:
        df: Raw orders DataFrame

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # Rename columns to match schema
    df.columns = df.columns.str.lower().str.strip()

    # Parse date
    df["order_date"] = pd.to_datetime(df["date"]).dt.date
    df = df.drop(columns=["date"])

    # Parse currency
    df["order_amount"] = df["order_amount"].apply(parse_currency)

    # Parse delivery hour
    df["delivery_hour"] = pd.to_datetime(
        df["delivery_hour"], format="%H:%M:%S", errors="coerce"
    ).dt.time

    # Ensure integers
    df["items_delivered"] = pd.to_numeric(df["items_delivered"], errors="coerce").fillna(0).astype(int)
    df["items_missing"] = pd.to_numeric(df["items_missing"], errors="coerce").fillna(0).astype(int)

    # Clean string columns
    df["region"] = df["region"].str.strip()
    df["driver_id"] = df["driver_id"].str.strip()
    df["customer_id"] = df["customer_id"].str.strip()
    df["order_id"] = df["order_id"].str.strip()

    return df


def transform_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform customers DataFrame.

    Args:
        df: Raw customers DataFrame

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Clean strings
    df["customer_id"] = df["customer_id"].str.strip()
    df["customer_name"] = df["customer_name"].str.strip()

    # Ensure age is integer
    df["customer_age"] = pd.to_numeric(df["customer_age"], errors="coerce").astype("Int64")

    return df


def transform_drivers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform drivers DataFrame.

    Args:
        df: Raw drivers DataFrame

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Clean strings
    df["driver_id"] = df["driver_id"].str.strip()
    df["driver_name"] = df["driver_name"].str.strip()

    # Ensure integers
    df["age"] = pd.to_numeric(df["age"], errors="coerce").astype("Int64")
    df["trips"] = pd.to_numeric(df["trips"], errors="coerce").fillna(0).astype(int)

    return df


def transform_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform products DataFrame.

    Note: The source CSV has a typo "produc_id" instead of "product_id"

    Args:
        df: Raw products DataFrame

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Fix column name typo
    if "produc_id" in df.columns:
        df = df.rename(columns={"produc_id": "product_id"})

    # Clean strings
    df["product_id"] = df["product_id"].str.strip()
    df["product_name"] = df["product_name"].str.strip()
    df["category"] = df["category"].str.strip()

    # Parse price
    df["price"] = df["price"].apply(parse_currency)

    return df


def transform_missing_items(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform missing items DataFrame.

    Args:
        df: Raw missing items DataFrame

    Returns:
        Transformed DataFrame
    """
    df = df.copy()

    # Normalize column names
    df.columns = df.columns.str.lower().str.strip()

    # Clean strings
    df["order_id"] = df["order_id"].str.strip()

    # Clean product IDs (handle NaN)
    for col in ["product_id_1", "product_id_2", "product_id_3"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.strip() if pd.notna(x) and isinstance(x, str) else x)

    return df


def transform_all(data: dict) -> dict:
    """
    Transform all datasets.

    Args:
        data: Dictionary with raw DataFrames

    Returns:
        Dictionary with transformed DataFrames
    """
    return {
        "orders": transform_orders(data["orders"]),
        "customers": transform_customers(data["customers"]),
        "drivers": transform_drivers(data["drivers"]),
        "products": transform_products(data["products"]),
        "missing_items": transform_missing_items(data["missing_items"]),
    }


def validate_data(data: dict) -> Tuple[bool, list]:
    """
    Validate transformed data for consistency.

    Checks:
    - Foreign key relationships
    - Data types
    - Value ranges

    Args:
        data: Dictionary with transformed DataFrames

    Returns:
        Tuple of (is_valid, list of issues)
    """
    issues = []

    orders = data["orders"]
    customers = data["customers"]
    drivers = data["drivers"]
    products = data["products"]
    missing_items = data["missing_items"]

    # Check foreign keys
    invalid_drivers = set(orders["driver_id"]) - set(drivers["driver_id"])
    if invalid_drivers:
        issues.append(f"Orders have {len(invalid_drivers)} invalid driver_ids")

    invalid_customers = set(orders["customer_id"]) - set(customers["customer_id"])
    if invalid_customers:
        issues.append(f"Orders have {len(invalid_customers)} invalid customer_ids")

    invalid_orders = set(missing_items["order_id"]) - set(orders["order_id"])
    if invalid_orders:
        issues.append(f"Missing items have {len(invalid_orders)} invalid order_ids")

    # Check value ranges
    if (orders["items_missing"] < 0).any():
        issues.append("Orders have negative items_missing values")

    if (orders["order_amount"] < 0).any():
        issues.append("Orders have negative order_amount values")

    if (drivers["age"] < 18).any():
        issues.append("Drivers have age below 18")

    return len(issues) == 0, issues

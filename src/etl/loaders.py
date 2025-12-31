"""
Data loaders for inserting data into PostgreSQL.
"""
import pandas as pd
from typing import Dict, Optional
from sqlalchemy import text

from src.config.database import engine, get_session
from src.database.models import Customer, Driver, Product, Order, MissingItem


def load_customers(df: pd.DataFrame, if_exists: str = "append") -> int:
    """
    Load customers data into PostgreSQL.

    Args:
        df: Transformed customers DataFrame
        if_exists: How to handle existing data ('fail', 'replace', 'append')

    Returns:
        Number of rows inserted
    """
    df.to_sql("customers", engine, if_exists=if_exists, index=False, method="multi")
    return len(df)


def load_drivers(df: pd.DataFrame, if_exists: str = "append") -> int:
    """
    Load drivers data into PostgreSQL.

    Args:
        df: Transformed drivers DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    df.to_sql("drivers", engine, if_exists=if_exists, index=False, method="multi")
    return len(df)


def load_products(df: pd.DataFrame, if_exists: str = "append") -> int:
    """
    Load products data into PostgreSQL.

    Args:
        df: Transformed products DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    df.to_sql("products", engine, if_exists=if_exists, index=False, method="multi")
    return len(df)


def load_orders(df: pd.DataFrame, if_exists: str = "append") -> int:
    """
    Load orders data into PostgreSQL.

    Args:
        df: Transformed orders DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    df.to_sql("orders", engine, if_exists=if_exists, index=False, method="multi")
    return len(df)


def load_missing_items(df: pd.DataFrame, if_exists: str = "append") -> int:
    """
    Load missing items data into PostgreSQL.

    Args:
        df: Transformed missing items DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    # Remove the id column if present (auto-generated)
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    df.to_sql("missing_items", engine, if_exists=if_exists, index=False, method="multi")
    return len(df)


def load_all(data: Dict[str, pd.DataFrame], truncate_first: bool = True) -> Dict[str, int]:
    """
    Load all data into PostgreSQL in correct order (respecting foreign keys).

    Args:
        data: Dictionary with transformed DataFrames
        truncate_first: If True, truncate tables before loading

    Returns:
        Dictionary with row counts per table
    """
    results = {}

    if truncate_first:
        truncate_all_tables()

    # Load in order of dependencies
    results["customers"] = load_customers(data["customers"], if_exists="append")
    results["drivers"] = load_drivers(data["drivers"], if_exists="append")
    results["products"] = load_products(data["products"], if_exists="append")
    results["orders"] = load_orders(data["orders"], if_exists="append")
    results["missing_items"] = load_missing_items(data["missing_items"], if_exists="append")

    return results


def truncate_all_tables():
    """Truncate all tables in correct order (respecting foreign keys)."""
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE missing_items CASCADE"))
        conn.execute(text("TRUNCATE TABLE orders CASCADE"))
        conn.execute(text("TRUNCATE TABLE products CASCADE"))
        conn.execute(text("TRUNCATE TABLE drivers CASCADE"))
        conn.execute(text("TRUNCATE TABLE customers CASCADE"))
        conn.commit()


def get_table_counts() -> Dict[str, int]:
    """Get row counts for all tables."""
    counts = {}
    tables = ["customers", "drivers", "products", "orders", "missing_items"]

    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            counts[table] = result.scalar()

    return counts


def upsert_order(order_data: dict) -> bool:
    """
    Upsert a single order (insert or update).

    Args:
        order_data: Dictionary with order fields

    Returns:
        True if successful
    """
    with get_session() as session:
        existing = session.query(Order).filter_by(order_id=order_data["order_id"]).first()

        if existing:
            for key, value in order_data.items():
                setattr(existing, key, value)
        else:
            order = Order(**order_data)
            session.add(order)

        return True

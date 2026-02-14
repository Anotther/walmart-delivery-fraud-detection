"""
Database connection module for Walmart Fraud Detection.
Provides functions to load data from PostgreSQL into DataFrames.
"""
import pandas as pd
from sqlalchemy import text
from typing import Dict, Optional

from src.config.database import engine as shared_engine


def get_engine():
    """Return shared SQLAlchemy engine for PostgreSQL connection pooling."""
    return shared_engine


def get_connection():
    """Return a raw SQLAlchemy connection from the shared engine."""
    return get_engine().connect()


def execute_query(query: str, params: Optional[Dict] = None) -> pd.DataFrame:
    """
    Execute SQL query and return results as DataFrame.

    Args:
        query: SQL query string
        params: Optional parameters for parameterized queries

    Returns:
        DataFrame with query results
    """
    with get_connection() as conn:
        return pd.read_sql(text(query), conn, params=params)


def load_orders() -> pd.DataFrame:
    """
    Load orders data from PostgreSQL with region name.

    Returns:
        DataFrame with orders data
    """
    query = """
    SELECT
        o.order_id::TEXT as order_id,
        o.order_date,
        o.order_amount,
        r.region_name as region,
        o.items_delivered,
        o.items_missing,
        o.delivery_hour,
        o.driver_id,
        o.customer_id,
        o.created_at
    FROM walmart_fraud.orders o
    LEFT JOIN walmart_fraud.regions r ON o.region_id = r.region_id
    ORDER BY o.order_date, o.delivery_hour
    """
    return execute_query(query)


def load_drivers() -> pd.DataFrame:
    """
    Load drivers data from PostgreSQL.

    Returns:
        DataFrame with drivers data
    """
    query = """
    SELECT
        driver_id,
        driver_name,
        driver_age as age,
        total_trips as trips
    FROM walmart_fraud.drivers
    ORDER BY driver_id
    """
    return execute_query(query)


def load_customers() -> pd.DataFrame:
    """
    Load customers data from PostgreSQL.

    Returns:
        DataFrame with customers data
    """
    query = """
    SELECT
        customer_id,
        customer_name,
        customer_age
    FROM walmart_fraud.customers
    ORDER BY customer_id
    """
    return execute_query(query)


def load_products() -> pd.DataFrame:
    """
    Load products data from PostgreSQL with category name.

    Returns:
        DataFrame with products data
    """
    query = """
    SELECT
        p.product_id,
        p.product_name,
        c.category_name as category,
        p.price
    FROM walmart_fraud.products p
    LEFT JOIN walmart_fraud.product_categories c ON p.category_id = c.category_id
    ORDER BY p.product_id
    """
    return execute_query(query)


def load_missing_items() -> pd.DataFrame:
    """
    Load missing items data from PostgreSQL (normalized format).

    Returns:
        DataFrame with missing items data
    """
    query = """
    SELECT
        mi.missing_item_id,
        mi.order_id::TEXT as order_id,
        mi.product_id,
        mi.item_position,
        p.product_name,
        p.price as product_price,
        c.category_name as category
    FROM walmart_fraud.order_missing_items mi
    LEFT JOIN walmart_fraud.products p ON mi.product_id = p.product_id
    LEFT JOIN walmart_fraud.product_categories c ON p.category_id = c.category_id
    ORDER BY mi.order_id, mi.item_position
    """
    return execute_query(query)


def load_missing_items_pivot() -> pd.DataFrame:
    """
    Load missing items in pivot format (product_id_1, product_id_2, product_id_3).
    Matches original CSV structure.

    Returns:
        DataFrame with pivoted missing items
    """
    query = """
    WITH ranked AS (
        SELECT
            order_id::TEXT as order_id,
            product_id,
            ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY item_position) as rn
        FROM walmart_fraud.order_missing_items
    )
    SELECT
        order_id,
        MAX(CASE WHEN rn = 1 THEN product_id END) as product_id_1,
        MAX(CASE WHEN rn = 2 THEN product_id END) as product_id_2,
        MAX(CASE WHEN rn = 3 THEN product_id END) as product_id_3
    FROM ranked
    GROUP BY order_id
    ORDER BY order_id
    """
    return execute_query(query)


def load_orders_full() -> pd.DataFrame:
    """
    Load orders with all related data (driver, customer, region).
    Denormalized view for analysis.

    Returns:
        DataFrame with full order details
    """
    query = """
    SELECT * FROM walmart_fraud.v_orders_full
    """
    return execute_query(query)


def load_driver_metrics() -> pd.DataFrame:
    """
    Load driver fraud metrics from view.

    Returns:
        DataFrame with driver fraud metrics
    """
    query = """
    SELECT * FROM walmart_fraud.v_driver_fraud_metrics
    """
    return execute_query(query)


def load_customer_metrics() -> pd.DataFrame:
    """
    Load customer fraud metrics from view.

    Returns:
        DataFrame with customer fraud metrics
    """
    query = """
    SELECT * FROM walmart_fraud.v_customer_fraud_metrics
    """
    return execute_query(query)


def load_all_data() -> Dict[str, pd.DataFrame]:
    """
    Load all data from PostgreSQL.

    Returns:
        Dictionary with all DataFrames:
        - orders: Orders data
        - drivers: Drivers data
        - customers: Customers data
        - products: Products data
        - missing_items: Missing items (normalized)
    """
    return {
        'orders': load_orders(),
        'drivers': load_drivers(),
        'customers': load_customers(),
        'products': load_products(),
        'missing_items': load_missing_items(),
    }


def get_summary_stats() -> Dict:
    """
    Get summary statistics from database.

    Returns:
        Dictionary with summary statistics
    """
    query = """
    SELECT
        (SELECT COUNT(*) FROM walmart_fraud.orders) as total_orders,
        (SELECT COUNT(*) FROM walmart_fraud.drivers) as total_drivers,
        (SELECT COUNT(*) FROM walmart_fraud.customers) as total_customers,
        (SELECT COUNT(*) FROM walmart_fraud.products) as total_products,
        (SELECT COUNT(*) FROM walmart_fraud.order_missing_items) as total_missing_items,
        (SELECT SUM(items_missing) FROM walmart_fraud.orders) as sum_items_missing,
        (SELECT SUM(order_amount) FROM walmart_fraud.orders) as total_order_value,
        (SELECT MIN(order_date) FROM walmart_fraud.orders) as min_date,
        (SELECT MAX(order_date) FROM walmart_fraud.orders) as max_date
    """
    result = execute_query(query)
    return result.iloc[0].to_dict()


def test_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    print("Testing database connection...")
    if test_connection():
        print("Connection successful!")

        # Print summary stats
        stats = get_summary_stats()
        print("\nDatabase Summary:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("Connection failed!")

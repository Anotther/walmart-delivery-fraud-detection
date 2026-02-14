"""
Data loaders for inserting data into PostgreSQL.
"""
import pandas as pd
from typing import Any, Dict, Optional
from sqlalchemy import text

from src.config.database import engine

SCHEMA = "walmart_fraud"

LOOKUP_MAP_QUERIES = {
    ("product_categories", "category_name", "category_id"): text(
        """
        SELECT category_name, category_id
        FROM walmart_fraud.product_categories
        """
    ),
    ("regions", "region_name", "region_id"): text(
        """
        SELECT region_name, region_id
        FROM walmart_fraud.regions
        """
    ),
}

LOOKUP_SET_QUERIES = {
    ("drivers", "driver_id"): text("SELECT driver_id FROM walmart_fraud.drivers"),
    ("customers", "customer_id"): text("SELECT customer_id FROM walmart_fraud.customers"),
    ("orders", "order_id::TEXT"): text("SELECT order_id::TEXT FROM walmart_fraud.orders"),
    ("products", "product_id"): text("SELECT product_id FROM walmart_fraud.products"),
}

TABLE_COUNT_QUERIES = {
    "customers": text("SELECT COUNT(*) FROM walmart_fraud.customers"),
    "drivers": text("SELECT COUNT(*) FROM walmart_fraud.drivers"),
    "products": text("SELECT COUNT(*) FROM walmart_fraud.products"),
    "orders": text("SELECT COUNT(*) FROM walmart_fraud.orders"),
    "order_missing_items": text("SELECT COUNT(*) FROM walmart_fraud.order_missing_items"),
}

REGION_ID_BY_NAME_QUERY = text(
    """
    SELECT region_id
    FROM walmart_fraud.regions
    WHERE region_name = :region_name
    """
)

UPSERT_ORDER_QUERY = text(
    """
    INSERT INTO walmart_fraud.orders (
        order_id, order_date, order_amount, region_id, items_delivered,
        items_missing, delivery_hour, driver_id, customer_id
    ) VALUES (
        :order_id, :order_date, :order_amount, :region_id, :items_delivered,
        :items_missing, :delivery_hour, :driver_id, :customer_id
    )
    ON CONFLICT (order_id) DO UPDATE SET
        order_date = EXCLUDED.order_date,
        order_amount = EXCLUDED.order_amount,
        region_id = EXCLUDED.region_id,
        items_delivered = EXCLUDED.items_delivered,
        items_missing = EXCLUDED.items_missing,
        delivery_hour = EXCLUDED.delivery_hour,
        driver_id = EXCLUDED.driver_id,
        customer_id = EXCLUDED.customer_id
    """
)


def _require_columns(df: pd.DataFrame, required: list[str], dataset_name: str) -> None:
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {missing}")


def _fetch_lookup_map(connection, table: str, key_col: str, value_col: str) -> Dict[str, Any]:
    query = LOOKUP_MAP_QUERIES.get((table, key_col, value_col))
    if query is None:
        raise ValueError(
            f"Unsupported lookup map request for table={table}, key_col={key_col}, value_col={value_col}"
        )
    rows = connection.execute(query).fetchall()
    return {str(row[0]): row[1] for row in rows}


def _fetch_lookup_set(connection, table: str, key_expr: str) -> set[str]:
    query = LOOKUP_SET_QUERIES.get((table, key_expr))
    if query is None:
        raise ValueError(
            f"Unsupported lookup set request for table={table}, key_expr={key_expr}"
        )
    rows = connection.execute(query).fetchall()
    return {str(row[0]) for row in rows}


def load_customers(df: pd.DataFrame, if_exists: str = "append", connection=None) -> int:
    """
    Load customers data into PostgreSQL.

    Args:
        df: Transformed customers DataFrame
        if_exists: How to handle existing data ('fail', 'replace', 'append')

    Returns:
        Number of rows inserted
    """
    _require_columns(df, ["customer_id", "customer_name", "customer_age"], "customers")
    payload = df[["customer_id", "customer_name", "customer_age"]].copy()
    payload["customer_id"] = payload["customer_id"].astype(str).str.strip()
    payload["customer_name"] = payload["customer_name"].astype(str).str.strip()
    payload["customer_age"] = pd.to_numeric(payload["customer_age"], errors="coerce")
    payload = payload.dropna(subset=["customer_id", "customer_name", "customer_age"])
    payload["customer_age"] = payload["customer_age"].astype(int)
    payload = payload.drop_duplicates(subset=["customer_id"])

    target = connection if connection is not None else engine
    payload.to_sql(
        "customers",
        target,
        schema=SCHEMA,
        if_exists=if_exists,
        index=False,
        method="multi",
    )
    return len(payload)


def load_drivers(df: pd.DataFrame, if_exists: str = "append", connection=None) -> int:
    """
    Load drivers data into PostgreSQL.

    Args:
        df: Transformed drivers DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    _require_columns(df, ["driver_id", "driver_name", "age", "trips"], "drivers")
    payload = df[["driver_id", "driver_name", "age", "trips"]].copy()
    payload = payload.rename(columns={"age": "driver_age", "trips": "total_trips"})
    payload["driver_id"] = payload["driver_id"].astype(str).str.strip()
    payload["driver_name"] = payload["driver_name"].astype(str).str.strip()
    payload["driver_age"] = pd.to_numeric(payload["driver_age"], errors="coerce")
    payload["total_trips"] = pd.to_numeric(payload["total_trips"], errors="coerce")
    payload = payload.dropna(subset=["driver_id", "driver_name", "driver_age", "total_trips"])
    payload["driver_age"] = payload["driver_age"].astype(int)
    payload["total_trips"] = payload["total_trips"].astype(int)
    payload = payload.drop_duplicates(subset=["driver_id"])

    target = connection if connection is not None else engine
    payload.to_sql(
        "drivers",
        target,
        schema=SCHEMA,
        if_exists=if_exists,
        index=False,
        method="multi",
    )
    return len(payload)


def load_products(df: pd.DataFrame, if_exists: str = "append", connection=None) -> int:
    """
    Load products data into PostgreSQL.

    Args:
        df: Transformed products DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    if connection is None:
        with engine.begin() as conn:
            return load_products(df=df, if_exists=if_exists, connection=conn)

    _require_columns(df, ["product_id", "product_name", "category", "price"], "products")
    payload = df[["product_id", "product_name", "category", "price"]].copy()
    payload["product_id"] = payload["product_id"].astype(str).str.strip()
    payload["product_name"] = payload["product_name"].astype(str).str.strip()
    payload["category"] = payload["category"].astype(str).str.strip()
    payload["price"] = pd.to_numeric(payload["price"], errors="coerce")
    payload = payload.dropna(subset=["product_id", "product_name", "category", "price"])
    payload = payload.drop_duplicates(subset=["product_id"])

    category_map = _fetch_lookup_map(
        connection=connection,
        table="product_categories",
        key_col="category_name",
        value_col="category_id",
    )
    payload["category_id"] = payload["category"].map(category_map)
    unknown_categories = sorted(payload[payload["category_id"].isna()]["category"].unique())
    if unknown_categories:
        raise ValueError(f"Unknown product categories not found in lookup table: {unknown_categories}")

    payload = payload[["product_id", "product_name", "category_id", "price"]]
    payload["category_id"] = payload["category_id"].astype(int)

    payload.to_sql(
        "products",
        connection,
        schema=SCHEMA,
        if_exists=if_exists,
        index=False,
        method="multi",
    )
    return len(payload)


def load_orders(df: pd.DataFrame, if_exists: str = "append", connection=None) -> int:
    """
    Load orders data into PostgreSQL.

    Args:
        df: Transformed orders DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    if connection is None:
        with engine.begin() as conn:
            return load_orders(df=df, if_exists=if_exists, connection=conn)

    required = [
        "order_id",
        "order_date",
        "order_amount",
        "region",
        "items_delivered",
        "items_missing",
        "delivery_hour",
        "driver_id",
        "customer_id",
    ]
    _require_columns(df, required, "orders")
    payload = df[required].copy()
    payload["order_id"] = payload["order_id"].astype(str).str.strip()
    payload["region"] = payload["region"].astype(str).str.strip()
    payload["driver_id"] = payload["driver_id"].astype(str).str.strip()
    payload["customer_id"] = payload["customer_id"].astype(str).str.strip()
    payload["order_date"] = pd.to_datetime(payload["order_date"], errors="coerce").dt.date
    payload["order_amount"] = pd.to_numeric(payload["order_amount"], errors="coerce")
    payload["items_delivered"] = pd.to_numeric(payload["items_delivered"], errors="coerce")
    payload["items_missing"] = pd.to_numeric(payload["items_missing"], errors="coerce")
    payload["delivery_hour"] = pd.to_datetime(
        payload["delivery_hour"].astype(str),
        format="%H:%M:%S",
        errors="coerce",
    ).dt.time
    payload = payload.dropna(
        subset=[
            "order_id",
            "order_date",
            "order_amount",
            "region",
            "items_delivered",
            "items_missing",
            "delivery_hour",
            "driver_id",
            "customer_id",
        ]
    )
    payload["items_delivered"] = payload["items_delivered"].astype(int)
    payload["items_missing"] = payload["items_missing"].astype(int)
    payload = payload.drop_duplicates(subset=["order_id"])

    region_map = _fetch_lookup_map(
        connection=connection,
        table="regions",
        key_col="region_name",
        value_col="region_id",
    )
    payload["region_id"] = payload["region"].map(region_map)
    unknown_regions = sorted(payload[payload["region_id"].isna()]["region"].unique())
    if unknown_regions:
        raise ValueError(f"Unknown regions not found in lookup table: {unknown_regions}")

    known_drivers = _fetch_lookup_set(connection, "drivers", "driver_id")
    known_customers = _fetch_lookup_set(connection, "customers", "customer_id")
    unknown_drivers = sorted(set(payload["driver_id"]) - known_drivers)
    unknown_customers = sorted(set(payload["customer_id"]) - known_customers)
    if unknown_drivers:
        raise ValueError(f"Orders contain unknown driver_id values: {unknown_drivers[:10]}")
    if unknown_customers:
        raise ValueError(f"Orders contain unknown customer_id values: {unknown_customers[:10]}")

    payload = payload[
        [
            "order_id",
            "order_date",
            "order_amount",
            "region_id",
            "items_delivered",
            "items_missing",
            "delivery_hour",
            "driver_id",
            "customer_id",
        ]
    ]
    payload["region_id"] = payload["region_id"].astype(int)

    payload.to_sql(
        "orders",
        connection,
        schema=SCHEMA,
        if_exists=if_exists,
        index=False,
        method="multi",
    )
    return len(payload)


def load_missing_items(df: pd.DataFrame, if_exists: str = "append", connection=None) -> int:
    """
    Load missing items data into PostgreSQL.

    Args:
        df: Transformed missing items DataFrame
        if_exists: How to handle existing data

    Returns:
        Number of rows inserted
    """
    if connection is None:
        with engine.begin() as conn:
            return load_missing_items(df=df, if_exists=if_exists, connection=conn)

    _require_columns(df, ["order_id"], "missing_items")

    normalized_parts = []
    for item_position in (1, 2, 3):
        product_col = f"product_id_{item_position}"
        if product_col not in df.columns:
            continue

        part = df[["order_id", product_col]].dropna(subset=["order_id", product_col]).copy()
        part = part.rename(columns={product_col: "product_id"})
        part["item_position"] = item_position
        normalized_parts.append(part)

    if not normalized_parts:
        return 0

    payload = pd.concat(normalized_parts, ignore_index=True)
    payload["order_id"] = payload["order_id"].astype(str).str.strip()
    payload["product_id"] = payload["product_id"].astype(str).str.strip()
    payload = payload[(payload["order_id"] != "") & (payload["product_id"] != "")]
    payload = payload.drop_duplicates(subset=["order_id", "item_position"])

    known_order_ids = _fetch_lookup_set(connection, "orders", "order_id::TEXT")
    known_product_ids = _fetch_lookup_set(connection, "products", "product_id")
    unknown_orders = sorted(set(payload["order_id"]) - known_order_ids)
    unknown_products = sorted(set(payload["product_id"]) - known_product_ids)
    if unknown_orders:
        raise ValueError(
            f"Missing items contain unknown order_id values: {unknown_orders[:10]}"
        )
    if unknown_products:
        raise ValueError(
            f"Missing items contain unknown product_id values: {unknown_products[:10]}"
        )

    payload = payload[["order_id", "product_id", "item_position"]]
    payload["item_position"] = payload["item_position"].astype(int)
    payload.to_sql(
        "order_missing_items",
        connection,
        schema=SCHEMA,
        if_exists=if_exists,
        index=False,
        method="multi",
    )
    return len(payload)


def load_all(data: Dict[str, pd.DataFrame], truncate_first: bool = True) -> Dict[str, int]:
    """
    Load all data into PostgreSQL in correct order (respecting foreign keys).

    Args:
        data: Dictionary with transformed DataFrames
        truncate_first: If True, truncate tables before loading

    Returns:
        Dictionary with row counts per table
    """
    with engine.begin() as conn:
        if truncate_first:
            truncate_all_tables(connection=conn)

        # Load in order of dependencies
        results = {
            "customers": load_customers(data["customers"], if_exists="append", connection=conn),
            "drivers": load_drivers(data["drivers"], if_exists="append", connection=conn),
            "products": load_products(data["products"], if_exists="append", connection=conn),
            "orders": load_orders(data["orders"], if_exists="append", connection=conn),
            "order_missing_items": load_missing_items(
                data["missing_items"], if_exists="append", connection=conn
            ),
        }
        return results


def truncate_all_tables(connection=None):
    """Truncate all tables in correct order (respecting foreign keys)."""
    truncate_sql = text(
        """
        TRUNCATE TABLE
            walmart_fraud.order_missing_items,
            walmart_fraud.orders,
            walmart_fraud.products,
            walmart_fraud.drivers,
            walmart_fraud.customers
        RESTART IDENTITY CASCADE
        """
    )
    if connection is not None:
        connection.execute(truncate_sql)
        return

    with engine.begin() as conn:
        conn.execute(truncate_sql)


def get_table_counts() -> Dict[str, int]:
    """Get row counts for all tables."""
    counts = {}
    tables = ["customers", "drivers", "products", "orders", "order_missing_items"]

    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(TABLE_COUNT_QUERIES[table])
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
    payload = dict(order_data)
    required_fields = {
        "order_id",
        "order_date",
        "order_amount",
        "items_delivered",
        "items_missing",
        "delivery_hour",
        "driver_id",
        "customer_id",
    }
    missing = required_fields - set(payload.keys())
    if missing:
        raise ValueError(f"Missing required order fields: {sorted(missing)}")

    if "region_id" not in payload:
        region_value = payload.get("region")
        if region_value is None:
            raise ValueError("order_data must contain either 'region_id' or 'region'")

        with engine.connect() as conn:
            region_id = conn.execute(
                REGION_ID_BY_NAME_QUERY,
                {"region_name": str(region_value)},
            ).scalar()
        if region_id is None:
            raise ValueError(f"Unknown region: {region_value}")
        payload["region_id"] = int(region_id)

    params = {
        "order_id": str(payload["order_id"]),
        "order_date": payload["order_date"],
        "order_amount": payload["order_amount"],
        "region_id": int(payload["region_id"]),
        "items_delivered": int(payload["items_delivered"]),
        "items_missing": int(payload["items_missing"]),
        "delivery_hour": payload["delivery_hour"],
        "driver_id": str(payload["driver_id"]),
        "customer_id": str(payload["customer_id"]),
    }
    with engine.begin() as conn:
        conn.execute(UPSERT_ORDER_QUERY, params)

    return True

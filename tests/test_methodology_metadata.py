import pandas as pd

import src.dashboard.data_cache as data_cache_module
from src.dashboard.data_cache import DashboardCache


def _patch_loaders(monkeypatch, orders, drivers, customers, products):
    monkeypatch.setattr(data_cache_module, "load_orders", lambda: orders.copy())
    monkeypatch.setattr(data_cache_module, "load_drivers", lambda: drivers.copy())
    monkeypatch.setattr(data_cache_module, "load_customers", lambda: customers.copy())
    monkeypatch.setattr(data_cache_module, "load_products", lambda: products.copy())


def _orders_columns():
    return [
        "order_id",
        "order_date",
        "order_amount",
        "region",
        "items_delivered",
        "items_missing",
        "delivery_hour",
        "driver_id",
        "customer_id",
        "created_at",
    ]


def test_get_methodology_metadata_contract_nominal(monkeypatch):
    orders = pd.DataFrame(
        [
            {
                "order_id": "O-1",
                "order_date": "2023-01-01",
                "order_amount": 120.0,
                "region": "Orlando",
                "items_delivered": 10,
                "items_missing": 1,
                "delivery_hour": "10:00:00",
                "driver_id": "",
                "customer_id": "C-1",
                "created_at": "2023-01-01 10:00:00",
            },
            {
                "order_id": "O-2",
                "order_date": "2023-01-02",
                "order_amount": -5.0,
                "region": "Orlando",
                "items_delivered": 8,
                "items_missing": 2,
                "delivery_hour": "11:00:00",
                "driver_id": "D-2",
                "customer_id": None,
                "created_at": "2023-01-02 10:00:00",
            },
            {
                "order_id": "O-3",
                "order_date": "2260-01-01",
                "order_amount": 90.0,
                "region": "Orlando",
                "items_delivered": 7,
                "items_missing": 0,
                "delivery_hour": "12:00:00",
                "driver_id": "D-3",
                "customer_id": "C-3",
                "created_at": "2023-01-03 10:00:00",
            },
        ]
    )
    drivers = pd.DataFrame(
        [
            {"driver_id": "D-1", "driver_name": "A", "age": 29, "trips": 12},
            {"driver_id": "D-2", "driver_name": "B", "age": None, "trips": 8},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "C-1", "customer_name": "U1", "customer_age": None},
            {"customer_id": "C-2", "customer_name": "U2", "customer_age": 31},
        ]
    )
    products = pd.DataFrame(
        [
            {"product_id": "P-1", "product_name": "A", "category": "Electronics", "price": 10.0},
            {"product_id": "P-2", "product_name": "B", "category": None, "price": 20.0},
        ]
    )

    _patch_loaders(monkeypatch, orders, drivers, customers, products)
    cache = DashboardCache(ttl_minutes=15)
    metadata = cache.get_methodology_metadata()

    legacy_keys = {
        "total_orders",
        "total_drivers",
        "total_customers",
        "total_products",
        "date_start",
        "date_end",
        "data_quality",
        "features",
    }
    new_keys = {
        "generated_at",
        "quality_score",
        "total_issues",
        "quality_issue_breakdown",
        "schema_catalog",
        "pipeline_steps",
        "feature_catalog",
    }
    assert legacy_keys.issubset(set(metadata.keys()))
    assert new_keys.issubset(set(metadata.keys()))
    assert 0.0 <= float(metadata["quality_score"]) <= 100.0

    breakdown = metadata["quality_issue_breakdown"]
    assert isinstance(breakdown, list)
    assert len(breakdown) >= 1
    required_issue_keys = {"issue", "count", "rate_pct", "severity"}
    for row in breakdown:
        assert required_issue_keys.issubset(set(row.keys()))
        assert isinstance(row["count"], int)
        assert isinstance(row["rate_pct"], float)
        assert row["severity"] in {"Critical", "High", "Medium", "Low"}

    dq = metadata["data_quality"]
    assert dq["orders_missing_driver"] == 1
    assert dq["orders_missing_customer"] == 1
    assert dq["orders_negative_amount"] == 1
    assert dq["orders_future_date"] == 1
    assert dq["drivers_missing_age"] == 1
    assert dq["customers_missing_age"] == 1
    assert dq["products_missing_category"] == 1


def test_get_methodology_metadata_zero_orders(monkeypatch):
    orders = pd.DataFrame(columns=_orders_columns())
    drivers = pd.DataFrame(columns=["driver_id", "driver_name", "age", "trips"])
    customers = pd.DataFrame(columns=["customer_id", "customer_name", "customer_age"])
    products = pd.DataFrame(columns=["product_id", "product_name", "category", "price"])

    _patch_loaders(monkeypatch, orders, drivers, customers, products)
    cache = DashboardCache(ttl_minutes=15)
    metadata = cache.get_methodology_metadata()

    assert metadata["total_orders"] == 0
    assert metadata["total_issues"] == 0
    assert metadata["quality_score"] == 100.0
    assert metadata["date_start"] == "N/A"
    assert metadata["date_end"] == "N/A"
    assert isinstance(metadata["quality_issue_breakdown"], list)
    assert all(item["rate_pct"] == 0.0 for item in metadata["quality_issue_breakdown"])


def test_get_methodology_metadata_missing_driver_customer_age(monkeypatch):
    orders = pd.DataFrame(
        [
            {
                "order_id": "O-1",
                "order_date": "2023-01-01",
                "order_amount": 120.0,
                "region": "Orlando",
                "items_delivered": 10,
                "items_missing": 1,
                "delivery_hour": "10:00:00",
                "driver_id": "D-1",
                "customer_id": "C-1",
                "created_at": "2023-01-01 10:00:00",
            }
        ]
    )
    drivers = pd.DataFrame(
        [
            {"driver_id": "D-1", "driver_name": "A", "age": None, "trips": 10},
            {"driver_id": "D-2", "driver_name": "B", "age": "", "trips": 7},
        ]
    )
    customers = pd.DataFrame(
        [
            {"customer_id": "C-1", "customer_name": "U1", "customer_age": None},
            {"customer_id": "C-2", "customer_name": "U2", "customer_age": ""},
        ]
    )
    products = pd.DataFrame(
        [{"product_id": "P-1", "product_name": "A", "category": "Electronics", "price": 10.0}]
    )

    _patch_loaders(monkeypatch, orders, drivers, customers, products)
    cache = DashboardCache(ttl_minutes=15)
    metadata = cache.get_methodology_metadata()

    dq = metadata["data_quality"]
    assert dq["drivers_missing_age"] == 2
    assert dq["customers_missing_age"] == 2
    assert "drivers_missing_age" in dq
    assert "orders_missing_driver" in dq


def test_get_methodology_metadata_rebuilds_legacy_cached_payload(monkeypatch):
    orders = pd.DataFrame(
        [
            {
                "order_id": "O-1",
                "order_date": "2023-01-01",
                "order_amount": 120.0,
                "region": "Orlando",
                "items_delivered": 10,
                "items_missing": 1,
                "delivery_hour": "10:00:00",
                "driver_id": "D-1",
                "customer_id": "C-1",
                "created_at": "2023-01-01 10:00:00",
            }
        ]
    )
    drivers = pd.DataFrame([{"driver_id": "D-1", "driver_name": "A", "age": 30, "trips": 10}])
    customers = pd.DataFrame([{"customer_id": "C-1", "customer_name": "U1", "customer_age": 31}])
    products = pd.DataFrame(
        [{"product_id": "P-1", "product_name": "A", "category": "Electronics", "price": 10.0}]
    )

    _patch_loaders(monkeypatch, orders, drivers, customers, products)
    cache = DashboardCache(ttl_minutes=15)
    cache._set_cache("methodology_metadata_v2", {"total_orders": 1})

    metadata = cache.get_methodology_metadata()
    assert "quality_issue_breakdown" in metadata
    assert "schema_catalog" in metadata
    assert "pipeline_steps" in metadata
    assert "feature_catalog" in metadata

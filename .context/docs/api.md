# API Reference

This repository does not expose HTTP endpoints.

## Public Runtime Interfaces
- `src/dashboard/data_cache.py`
  - `get_default_cache()`
  - `DashboardCache.get_page_data(page_name)`
  - `DashboardCache.get_orders_with_features()`
- `src/database/connection.py`
  - `execute_query(query, params=None)`
  - `load_orders()`, `load_drivers()`, `load_customers()`, `load_products()`, `load_missing_items()`

# Project Overview

## Purpose
Walmart Delivery Fraud Detection identifies suspicious delivery outcomes where customers report missing items. The project combines ETL, analytics, machine learning, and a Streamlit dashboard to support investigation and risk prioritization.

## Goals
- Quantify fraud exposure in Central Florida delivery operations.
- Distinguish likely driver, customer, and systemic risk signals.
- Prioritize investigation queues with transparent metrics.
- Provide an executive-friendly dashboard for continuous monitoring.

## Target Users
- Fraud analysts and operations investigators.
- Data team members maintaining ETL and feature pipelines.
- Product and operations stakeholders consuming dashboard insights.

## Main Capabilities
- CSV to PostgreSQL ETL pipeline (`src/etl/`, `scripts/run_etl.py`).
- Feature engineering by order, driver, customer, and time (`src/features/`).
- Risk modeling with outlier detection, clustering, and risk scoring (`src/models/`).
- Pattern analysis modules for temporal, geographic, and fraud behavior (`src/analysis/`).
- Multi-page Streamlit dashboard with cached data access (`dashboard/`, `src/dashboard/data_cache.py`).

## Data Scope
- `orders.csv`
- `customers_data.csv`
- `drivers_data.csv`
- `products_data.csv` (note: source column typo `produc_id` must be preserved)
- `missing_items_data.csv`

## Quick Start
1. Install dependencies: `pip install -r requirements.txt`
2. Configure PostgreSQL credentials in `.env`
3. Initialize database: `python scripts/setup_database.py`
4. (Optional) Re-run ETL: `python scripts/run_etl.py`
5. Train models: `python scripts/train_models.py`
6. Run dashboard: `streamlit run dashboard/app.py`

## Related Resources
- `README.md`
- `docs/architecture.md`
- `docs/data_dictionary.md`
- `docs/kpis_metrics.md`
- `.context/docs/architecture.md`

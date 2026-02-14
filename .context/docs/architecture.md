# Architecture Notes

## System Architecture Overview
The repository uses a modular Python monolith. Data enters from CSV files, flows through ETL into PostgreSQL, is transformed into features and risk signals, then is exposed through analytical modules and a Streamlit dashboard.

## Architectural Layers
- Data layer: `data/`, PostgreSQL schema in `src/database/sql/`.
- ETL layer: `src/etl/extractors.py`, `src/etl/transformers.py`, `src/etl/loaders.py`.
- Feature layer: `src/features/` modules for order, driver, customer, temporal, and aggregations.
- Modeling layer: `src/models/` for anomaly detection, clustering, and risk scoring.
- Analysis layer: `src/analysis/` for descriptive, temporal, geographic, and fraud pattern analyses.
- Presentation layer: `dashboard/` pages + `src/dashboard/` shared theme/cache utilities.

See `./codebase-map.json` for broader symbol inventory and structure metadata.

## Detected Design Patterns
| Pattern | Confidence | Locations | Description |
| --- | --- | --- | --- |
| Layered architecture | High | `src/etl`, `src/features`, `src/models`, `src/analysis` | Separates ingestion, transformation, modeling, and reporting concerns. |
| Repository/manager wrapper | High | `src/database/manager.py` | Centralizes DB sessions, query orchestration, and errors. |
| Cache facade | High | `src/dashboard/data_cache.py` | Provides dashboard-ready datasets and memoization boundaries. |
| Scripted pipeline entrypoints | High | `scripts/*.py` | Encodes repeatable ETL/train/report workflows for local execution. |

## Entry Points
- `scripts/setup_database.py`
- `scripts/run_etl.py`
- `scripts/train_models.py`
- `scripts/generate_report.py`
- `dashboard/app.py`

## Public API (Representative)
| Symbol | Type | Location |
| --- | --- | --- |
| `DatabaseManager` | class | `src/database/manager.py` |
| `DashboardCache` | class | `src/dashboard/data_cache.py` |
| `transform_all` | function | `src/etl/transformers.py` |
| `load_all` | function | `src/etl/loaders.py` |
| `analyze_all_fraud_patterns` | function | `src/analysis/fraud_patterns.py` |
| `aggregate_by_time_period` | function | `src/features/temporal_features.py` |
| `RiskScoringEngine` | class | `src/models/risk_scoring.py` |

## Internal System Boundaries
- Dashboard pages must read curated data through `src/dashboard/data_cache.py` (no direct CSV reads in pages).
- ETL transformation rules preserve source quirks where required by business context (`produc_id` typo).
- Feature and model modules should avoid direct UI coupling.

## External Service Dependencies
- PostgreSQL: transactional storage and analytical views.
- MLflow: experiment tracking for model iterations.
- Streamlit runtime: dashboard delivery.

## Key Decisions and Trade-offs
- Chosen stack favors fast iteration for analytics teams over distributed-service complexity.
- Materialized/cached dashboard datasets reduce UI latency at the cost of cache invalidation complexity.
- Non-supervised risk approaches increase discovery coverage but require analyst validation to control false positives.

## Top Directories Snapshot
- `src/`
- `dashboard/`
- `scripts/`
- `tests/`
- `docs/`
- `data/`
- `outputs/`
- `notebooks/`

## Related Resources
- `./project-overview.md`
- `./data-flow.md`
- `../../docs/architecture.md`

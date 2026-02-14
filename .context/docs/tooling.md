# Tooling and Productivity Guide

## Core Runtime
- Python 3.11+
- PostgreSQL
- Streamlit

## Key Python Dependencies
- Data: `pandas`, `numpy`, `sqlalchemy`, `psycopg2-binary`, `python-dotenv`
- ML: `scikit-learn`, `mlflow`
- Visualization: `plotly`, `matplotlib`, `seaborn`
- App: `streamlit`, `streamlit-option-menu`
- Testing: `pytest`

## Main Commands
- Install dependencies: `pip install -r requirements.txt`
- Setup DB and load data: `python scripts/setup_database.py`
- Run ETL pipeline: `python scripts/run_etl.py`
- Train models: `python scripts/train_models.py`
- Generate report: `python scripts/generate_report.py`
- Launch dashboard: `streamlit run dashboard/app.py`
- Run tests: `pytest tests/`

## Useful Project Utilities
- Theme audit: `scripts/audit_dashboard_theme.py`
- Dashboard data cache: `src/dashboard/data_cache.py`
- Visualization theme tokens: `src/config/viz_theme.py`

## Workflow Productivity Tips
- Use targeted pytest runs while iterating, then run full suite.
- Keep `docs/TASK_BACKLOG.md` updated to reduce cross-agent collisions.
- Keep doc updates close to code changes for durable context.

## Related Resources
- `../../requirements.txt`
- `./development-workflow.md`
- `../../AGENTS.md`

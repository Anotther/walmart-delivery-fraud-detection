# Deployment Notes

## Current Baseline
- The app entrypoint is `dashboard/app.py`.
- Database setup and ETL are executed via `scripts/setup_database.py` and `scripts/run_etl.py`.
- Security/quality checks can be run with `scripts/security_checks.sh`.

## Pre-Release Checklist
- `pytest tests/`
- `scripts/security_checks.sh`
- Manual smoke run: `streamlit run dashboard/app.py`

## Operational Constraints
- Keep secrets in `.env` only.
- Do not run with `APP_ENV=production` and `DEBUG=True` (debug is forced off in production code path).

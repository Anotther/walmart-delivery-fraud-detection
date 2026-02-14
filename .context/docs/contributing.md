# Contributing

## Development Flow
1. Install dependencies: `pip install -r requirements.txt`
2. Run tests: `pytest tests/`
3. Run security checks: `scripts/security_checks.sh`

## Conventions
- Python style: PEP 8
- Naming: `snake_case` for functions/variables, `PascalCase` for classes
- Dashboard pages use numeric prefixes (for example `1_Overview.py`)

## Validation
- For dashboard changes, run manual checklist from `docs/PLAN-dashboard-streamlit.md`.

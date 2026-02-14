# Testing Strategy

## Testing Framework
- Primary framework: `pytest`.
- Test location: `tests/`.
- Naming convention: `test_*.py`.

## Current Automated Coverage
- `tests/test_temporal_anomalies.py`: temporal anomaly behavior checks.
- `tests/test_methodology_metadata.py`: methodology metadata contract tests.
- `tests/dashboard/test_theme_tokens.py`: theme token and contrast contract checks.
- `tests/dashboard/test_theme_audit.py`: dashboard theme audit checks.

## Recommended Test Scope for Changes
- ETL updates: add transform/load unit tests for edge cases and typing.
- Feature updates: add deterministic tests for metric calculations.
- Model helper updates: validate score ranges and fallback behavior.
- Dashboard updates: run existing dashboard tests plus manual UI checklist.

## Manual Validation
For UI-related work, execute `docs/PLAN-dashboard-streamlit.md` checklist and verify:
- Page load without exceptions.
- Filters produce expected scoped outputs.
- Theme colors and contrast remain compliant.
- KPI values remain consistent with data-cache outputs.

## Command Set
- Full suite: `pytest tests/`
- Targeted file: `pytest tests/dashboard/test_theme_tokens.py`
- Optional smoke run: `streamlit run dashboard/app.py`

## Quality Gates
- No failing tests in touched areas.
- New logic should have at least one direct test when practical.
- Manual dashboard checks documented for UI changes.

## Related Resources
- `./development-workflow.md`
- `../../docs/PLAN-dashboard-streamlit.md`

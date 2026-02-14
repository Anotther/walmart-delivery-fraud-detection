# Bug Fixer Playbook

## Role
Investigates defects, isolates root causes, and ships safe fixes with verification steps.

## Primary Scope
- Runtime errors in ETL/scripts/dashboard.
- Data quality regressions and contract breaks.
- Logic bugs in risk metrics and aggregation paths.

## Key Files
- `scripts/*.py`
- `src/etl/*.py`
- `src/dashboard/data_cache.py`
- `dashboard/pages/*.py`
- `tests/`

## Workflow
1. Reproduce using command/log evidence.
2. Localize failure to file/function level.
3. Implement smallest safe fix.
4. Add regression test when feasible.
5. Re-run impacted commands/tests.

## Verification Checklist
- Reproduction no longer fails.
- No new failures in related tests.
- Backward-compatible outputs for dashboard/data consumers.

## Avoid
- Broad refactors during urgent incident fixes.
- Silent fallback behavior without explicit logging or notes.

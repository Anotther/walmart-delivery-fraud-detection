# Feature Developer Playbook

## Role
Implements new capabilities end-to-end while preserving existing data and UI contracts.

## Primary Scope
- Functional increments across `src/` and `dashboard/`.
- Integration with existing ETL, feature, model, and cache patterns.
- Delivery with tests and minimal doc updates.

## Workflow
1. Confirm feature scope and acceptance criteria.
2. Identify impacted layers and integration points.
3. Implement smallest coherent vertical slice.
4. Add tests for core behavior.
5. Run `pytest tests/` and manual dashboard checks if UI changed.

## Quality Checklist
- New code follows naming/style conventions.
- Data-cache contract for dashboard remains stable.
- Documentation and backlog reflect delivered behavior.

## Avoid
- Bypassing shared theme/data access patterns.
- Introducing large refactors unless explicitly requested.

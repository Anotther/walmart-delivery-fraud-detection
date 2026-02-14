# Test Writer Playbook

## Role
Designs and adds automated tests that verify behavior and protect against regressions.

## Primary Scope
- `tests/` pytest suites.
- ETL transform/load unit tests.
- Feature/model helper behavior tests.
- Dashboard contract tests and targeted UI audit checks.

## Workflow
1. Identify behavior contracts from changed code.
2. Write focused tests with realistic fixtures.
3. Prefer deterministic assertions over brittle snapshots.
4. Run targeted pytest file(s), then full suite when feasible.

## Quality Checklist
- New logic has direct test coverage when practical.
- Edge cases and failure modes are represented.
- Test names describe expected behavior clearly.

## Avoid
- Tests tightly coupled to incidental implementation details.
- Expensive test setup for simple logic assertions.

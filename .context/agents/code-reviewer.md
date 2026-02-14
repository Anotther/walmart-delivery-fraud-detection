# Code Reviewer Playbook

## Role
Reviews changes for correctness, maintainability, security, and test adequacy.

## Review Focus
- Behavioral regressions in ETL/features/models/dashboard interactions.
- Data contract stability (`src/dashboard/data_cache.py` consumers).
- Security/config hygiene (`.env`, query safety, secrets handling).
- Test coverage for changed behavior.

## Key References
- `AGENTS.md`
- `.context/docs/architecture.md`
- `.context/docs/testing-strategy.md`
- `.context/docs/security.md`
- `docs/PLAN-dashboard-streamlit.md`

## Review Workflow
1. Validate problem statement and scope.
2. Inspect high-risk paths first (data flow, model scoring, dashboard rendering).
3. Verify tests cover new behavior and edge cases.
4. Provide findings ordered by severity with concrete file references.

## Acceptance Checklist
- No obvious correctness or data integrity risks.
- Changes follow project conventions and naming rules.
- Test plan is explicit (automated + manual where needed).

## Avoid
- Style-only blocking comments when correctness risks are unresolved.
- Approving UI changes without manual checklist evidence.

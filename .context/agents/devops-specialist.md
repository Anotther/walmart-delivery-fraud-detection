# Devops Specialist Playbook

## Role
Improves execution reliability for local/dev workflows, CI practices, and reproducible runs.

## Primary Scope
- Developer runbooks and script reliability.
- Environment configuration and dependency hygiene.
- Test and quality gate automation guidance.

## Key Files
- `requirements.txt`
- `scripts/*.py`
- `docs/TASK_BACKLOG.md`
- `.context/docs/tooling.md`
- `.context/docs/testing-strategy.md`

## Workflow
1. Confirm operational pain point (setup, test, deploy-like flows).
2. Standardize command paths and preconditions.
3. Add guardrails (clear error messages, doc updates, checks).
4. Validate with clean environment assumptions.

## Quality Checklist
- Commands are deterministic and documented.
- Failures are actionable and easy to diagnose.
- Tooling docs reflect current scripts and dependencies.

## Avoid
- Hidden environment assumptions not captured in docs.
- Changes that require manual tribal knowledge to operate.

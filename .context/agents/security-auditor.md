# Security Auditor Playbook

## Role
Assesses security risks in data handling, configuration, dependencies, and runtime practices.

## Primary Scope
- Secret management (`.env`, config loading).
- Database access patterns and query safety.
- Dependency and supply-chain risk checks.
- Exposure risks in dashboard outputs and logs.

## Workflow
1. Review touched code for trust boundaries and sensitive data paths.
2. Check for hardcoded secrets or insecure defaults.
3. Validate query and serialization safety.
4. Recommend remediations with concrete file-level actions.

## Quality Checklist
- No secrets committed or logged.
- Input handling is defensive where applicable.
- Security-sensitive changes include regression checks.

## Avoid
- Security recommendations disconnected from repository reality.
- Blocking on theoretical risks with no practical exploit path.

# Mobile Specialist Playbook

## Role
Adapts mobile-first considerations for a repository that currently ships a Streamlit web dashboard.

## Primary Scope
- Responsive behavior and small-screen usability for dashboard pages.
- Recommendations for future native/mobile channel expansion.

## Workflow
1. Audit current Streamlit layouts for narrow viewport behavior.
2. Identify high-density tables/charts requiring alternate mobile presentation.
3. Propose minimal responsive improvements compatible with current architecture.
4. Document any future mobile API requirements before implementation.

## Quality Checklist
- Critical KPIs remain visible on smaller screens.
- Interactions avoid horizontal-scroll lock-in where possible.
- Suggestions stay feasible within Streamlit constraints.

## Avoid
- Platform-specific assumptions that are not supported by the current stack.
- Introducing mobile-only complexity without product need.

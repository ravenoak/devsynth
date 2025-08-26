# In-Repo Issue Tracking

This directory contains the active ticketing system for DevSynth. It does not integrate with GitHub Issues.

References:
- .junie/guidelines.md (style, typing, testing discipline)
- docs/plan.md (stabilization priorities)
- docs/roadmap/milestones/0.1.0a1.md (current milestone)
- docs/tasks.md (authoritative checklist to link from tickets)

## Naming Conventions

- Each ticket filename is a slug of its title (e.g., `CLI-and-UI-improvements.md`).
- The first line must be `# <title>`.

## Ticket Template

- Start new tickets by copying `TEMPLATE.md` and renaming it to a slug of its title.
- Populate the Milestone, Status, Priority, Owner, Labels, Dependencies, Problem Statement, Acceptance Criteria, Action Plan, Progress, and References sections.
- Reference archived dependencies with `archived/<slug>.md` paths.
- Update a ticket's `Status` when all dependencies are resolved.

## Owners and Labels (Required)

- Owner: a person or handle responsible for delivery (e.g., `@dev`).
- Labels (choose 1+):
  - area:cli | area:testing | area:docs | area:providers | area:webui | area:infra
  - type:bug | type:enhancement | type:task | type:refactor | type:flaky
  - risk:low | risk:medium | risk:high
- Link to tasks: include related item numbers from docs/tasks.md (e.g., `Tasks: 5, 23, 35`).

## Triage Workflow

1. Intake: ensure required fields (Owner, Labels, Acceptance Criteria) are present.
2. Milestone assignment: set `Milestone: 0.1.0a1` for near-term priorities.
3. Cross-link: add references to docs/tasks.md items and relevant docs (e.g., .junie/guidelines.md sections).
4. Status flow: `proposed → in-progress → blocked (optional) → done → archived`.
5. Archive: when `done`, move file to `archived/<slug>.md` (immutable).

## Archive Policy

- When a ticket is closed, move it to `archived/<slug>.md`.
- Archived files are immutable; open new tickets for follow-up work.
- Archived tickets use the legacy format `# Issue <number>: <title>`.

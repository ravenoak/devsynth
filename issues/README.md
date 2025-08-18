# In-Repo Issue Tracking

This directory contains the active ticketing system for DevSynth. It does not integrate with GitHub Issues.

## Naming Conventions

- Each ticket filename is a slug of its title (e.g., `CLI-and-UI-improvements.md`).
- The first line must be `# <title>`.

## Ticket Template

- Start new tickets by copying `TEMPLATE.md` and renaming it to a slug of its title.
- Populate the Milestone, Status, Priority, Dependencies, Progress, and References sections.
- Reference archived dependencies with `archived/<slug>.md` paths.
- Update a ticket's `Status` when all dependencies are resolved.

## Archive Policy

- When a ticket is closed, move it to `archived/<slug>.md`.
- Archived files are immutable; open new tickets for follow-up work.
- Archived tickets use the legacy format `# Issue <number>: <title>`.

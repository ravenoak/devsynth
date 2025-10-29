---
title: "Atomic-Rewrite (Baseline)"
date: 2025-08-24
version: 0.1.0a1
status: active
last_reviewed: 2025-08-24
---

# Atomic‑Rewrite (Baseline)

The Atomic‑Rewrite baseline provides a minimal, feature‑gated CLI workflow to rewrite commit history into atomic commits. Advanced capabilities are intentionally gated and will expand in later releases.

- Scope: baseline stub integrated with the CLI
- Safety: disabled by default and gated by a feature flag
- UX: dry‑run supported to preview behavior

## Enabling the Feature

This feature is off by default. Enable it with:

```bash
devsynth config enable-feature atomic_rewrite
```

To verify feature state (informal check), run the command without enabling and observe the guidance message.

## Usage

```bash
# Show help
devsynth atomic-rewrite --help

# Dry run (no changes)
devsynth atomic-rewrite --path . --dry-run

# Create a new branch with rewritten history (baseline placeholder)
devsynth atomic-rewrite --path . --branch-name atomic
```

Notes:
- The baseline implementation performs minimal operations suitable for smoke validation. Future iterations will add analysis, clustering, and safety checks.
- Advanced paths remain behind the feature flag and may require additional extras in future versions.

## Rationale and Alignment
- Follows optional-by-default and lazy import principles
- Integrates with existing MVUU utilities but exposes a top‑level entry for discoverability
- Matches project guidelines (project guidelines) and the improvement plan (docs/plan.md)

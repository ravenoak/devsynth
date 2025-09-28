---
title: "MVUU Dashboard"
date: "2025-08-05"
version: "0.1.0-alpha.1"
tags:
  - "analysis"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-10-20"
---

# MVUU Dashboard

The MVUU dashboard provides an interactive view of commit traceability data
stored in a local `traceability.json` file (not committed to the repository). It
lists available TraceIDs and shows the linked issue and affected files for each
entry.

![MVUU Dashboard](mvuu_dashboard.svg)

## Usage

To populate the dashboard, DevSynth generates a fresh traceability report:

```bash
$ devsynth mvu report --output traceability.json
```

The `mvuu-dashboard` command runs this step automatically and then launches a
NiceGUI application that reads `traceability.json` and displays TraceIDs,
affected files, and related issues:

```bash
$ devsynth mvuu-dashboard
```

If report generation fails, the dashboard falls back to any existing
`traceability.json`.

## Autoresearch Enhancements

Autoresearch workflows extend the dashboard with optional overlays:

- **Research Timeline Layer** — displays knowledge graph queries, agent role
  transitions, and MVUU TraceIDs along a shared timeline so reviewers can follow
  how investigations evolved.
- **Provenance Filters** — add toggles that isolate traces involving research
  artefacts, letting teams focus on Autoresearch outcomes without losing standard
  traceability views.
- **Integrity Checks** — surface checksum and signature fields emitted by the
  CLI so reviewers can verify that research artefacts rendered in the dashboard
  match the underlying knowledge graph data.

These overlays are disabled by default; teams enable them via the `--research-metrics` CLI flag or a dashboard toggle. When active, the dashboard queries the
knowledge graph to fetch supporting artefacts and annotates TraceIDs with
bibliographic context, ensuring Autoresearch remains auditable without
sacrificing day-to-day usability.

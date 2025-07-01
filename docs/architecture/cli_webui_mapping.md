---
title: "CLI to WebUI Command Mapping"
date: "2025-06-19"
version: "1.0.0"
tags:
  - "architecture"
  - "ux"
  - "cli"
  - "webui"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-19"
---

# CLI ↔ WebUI Command Mapping

The table below maps each DevSynth CLI command to the WebUI page or action that
executes the same workflow. `N/A` indicates that no equivalent page is currently
available. All WebUI pages use the `UXBridge` abstraction to reuse the CLI's
backend functions.

| CLI Command / Subcommand  | WebUI Page / Action                                   |
|---------------------------|-------------------------------------------------------|
| `init`                    | **Onboarding** – Initialize Project form             |
| `spec`                    | **Requirements** – Generate Specs form               |
| `test`                    | **Synthesis** – Generate Tests form                  |
| `code`                    | **Synthesis** – Generate Code button                 |
| `run-pipeline`            | **Synthesis** – Run Pipeline button                  |
| `config`                  | **Config** – Update/View Configuration               |
| `config enable-feature`   | **Config** – Manage Feature Flags                    |
| `inspect`                 | **Requirements** – Inspect Requirements form         |
| `gather`                  | **Requirements** – Requirements Plan Wizard          |
| `wizard`                  | **Requirements** – Requirements Wizard               |
| `inspect-code`            | **Analysis** – Inspect Code form                     |
| `refactor`                | N/A (planned **Analysis** workflow suggestions)      |
| `webapp`                  | N/A (planned **Database/Web App** helper page)       |
| `serve`                   | N/A (planned server management page; currently runs API server from CLI)                       |
| `dbschema`                | N/A (planned **Database** helper page)               |
| `doctor` / `check`        | **Doctor** – Diagnostics page   |
| `edrr-cycle`              | **EDRR Cycle** – Cycle execution page   |
| `align`                   | **Alignment** – SDLC consistency checks   |
| `alignment-metrics`       | N/A (planned **Reports** page)                       |
| `inspect-config`          | N/A (configuration analysis section)                 |
| `validate-manifest`       | N/A (planned configuration validation)               |
| `validate-metadata`       | N/A (planned configuration validation)               |
| `test-metrics`            | N/A (planned test metrics report)                    |
| `generate-docs`           | N/A (planned **Synthesis** docs generation)          |
| `ingest`                  | N/A (planned project ingestion form)                 |
| `apispec`                 | N/A (planned API specification form)                 |
| `webui`                   | Launches the WebUI                                   |

The following CLI commands remain **N/A** in the WebUI (all planned for future integration):

- `refactor` (planned)
- `webapp` (planned)
- `serve` (planned)
- `dbschema` (planned)
- `alignment-metrics` (planned)
- `inspect-config` (planned)
- `validate-manifest` (planned)
- `validate-metadata` (planned)
- `test-metrics` (planned)
- `generate-docs` (planned)
- `ingest` (planned)
- `apispec` (planned)

Planned pages will integrate these commands into the WebUI. The `refactor` command is expected to appear in the **Analysis** section for automated improvement suggestions. A new operations page will manage the API server for `serve`, and `dbschema` will hook into the **Database** helper page for schema visualization.

Because each page calls workflow functions through the `UXBridge` layer,
adding UI support for these commands later only requires new pages that
invoke the same shared functions.

Terminology across the CLI and WebUI is kept consistent. For example, the
interactive workflow started by `gather` is called the *Requirements Plan
Wizard* in both interfaces.

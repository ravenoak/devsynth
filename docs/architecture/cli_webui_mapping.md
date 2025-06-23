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
| `analyze-code`            | **Analysis** – Analyze Code form                     |
| `refactor`                | N/A (planned **Analysis** workflow suggestions)      |
| `webapp`                  | N/A (planned **Database/Web App** helper page)       |
| `serve`                   | N/A (runs API server from CLI)                       |
| `dbschema`                | N/A (planned **Database** helper page)               |
| `doctor` / `check`        | N/A (planned configuration validation)               |
| `edrr-cycle`              | N/A (planned **EDRR Cycle** page)                    |
| `align`                   | N/A (planned **Reports** page)                       |
| `alignment-metrics`       | N/A (planned **Reports** page)                       |
| `analyze-manifest`        | N/A (planned configuration analysis section)         |
| `analyze-config`          | N/A (alias of `analyze-manifest`)                    |
| `validate-manifest`       | N/A (planned configuration validation)               |
| `validate-metadata`       | N/A (planned configuration validation)               |
| `test-metrics`            | N/A (planned test metrics report)                    |
| `generate-docs`           | N/A (planned **Synthesis** docs generation)          |
| `ingest`                  | N/A (planned project ingestion form)                 |
| `apispec`                 | N/A (planned API specification form)                 |
| `webui`                   | Launches the WebUI                                   |

The following CLI commands remain **N/A** in the WebUI:

- `refactor`
- `webapp`
- `serve`
- `dbschema`
- `doctor` / `check`
- `edrr-cycle`
- `align`
- `alignment-metrics`
- `analyze-manifest`
- `analyze-config`
- `validate-manifest`
- `validate-metadata`
- `test-metrics`
- `generate-docs`
- `ingest`
- `apispec`

Because each page calls workflow functions through the `UXBridge` layer,
adding UI support for these commands later only requires new pages that
invoke the same shared functions.

Terminology across the CLI and WebUI is kept consistent. For example, the
interactive workflow started by `gather` is called the *Requirements Plan
Wizard* in both interfaces.

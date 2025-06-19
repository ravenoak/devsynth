---
title: "CLI to WebUI Command Mapping"
date: "2025-06-18"
version: "1.0.0"
tags:
  - "architecture"
  - "ux"
  - "cli"
  - "webui"
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-06-18"
---

# CLI ↔ WebUI Command Mapping

The table below maps each DevSynth CLI command to the WebUI page or action that
executes the same workflow. All WebUI pages rely on the `UXBridge` abstraction
to reuse the CLI's backend functions.

| CLI Command               | WebUI Page / Action                           |
|---------------------------|-----------------------------------------------|
| `init`                    | **Onboarding** page – Initialize Project form |
| `spec`                    | **Requirements** page – Generate Specs form   |
| `inspect`                 | **Requirements** page – Inspect Requirements  |
| `wizard`                  | **Requirements** page – Requirements Wizard   |
| `gather`                  | **Requirements** page – Project Plan Wizard   |
| `test`                    | **Synthesis** page – Generate Tests form      |
| `code`                    | **Synthesis** page – Generate Code button     |
| `run-pipeline`            | **Synthesis** page – Run Pipeline button      |
| `config`                  | **Config** page – Update/View Configuration   |
| `analyze-code`            | **Analysis** page – Analyze Code form         |
| `webui`                   | Launches the WebUI                            |

## Workflows Missing WebUI Support

Several CLI workflows are not yet represented in the WebUI. The table below
lists the missing commands along with proposed locations in the interface:

| CLI Command(s)                           | Proposed WebUI Location / Action                     |
|-----------------------------------------|------------------------------------------------------|
| `edrr-cycle`                            | New **EDRR Cycle** page under **Analysis**           |
| `align`, `alignment-metrics`            | **Reports** page for SDLC alignment metrics          |
| `analyze-manifest`, `analyze-config`    | **Config** page – Manifest analysis section          |
| `generate-docs`                         | **Synthesis** page – Add “Generate Docs” button      |
| `ingest`                                | **Synthesis** page – Project ingestion form          |
| `apispec`                               | **Synthesis** page – API specification form          |
| `doctor`, `check`                       | **Config** page – Validation utility                 |
| `validate-manifest`, `validate-metadata`| **Config** page – Validation utility                 |
| `test-metrics`                          | **Analysis** page – Test metrics report              |
| `refactor`                              | **Analysis** page – Workflow suggestions             |
| `webapp`, `serve`, `dbschema`           | New **Database** helper page                         |

Adding these pages or sidebar entries would provide complete parity. Where
appropriate, terminology should mirror the CLI (e.g., “EDRR Cycle”) to avoid
confusion.

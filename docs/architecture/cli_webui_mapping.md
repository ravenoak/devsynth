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

Several CLI workflows are not yet represented in the WebUI:

- `edrr-cycle`
- `align` and `alignment-metrics`
- `analyze-manifest`
- `generate-docs`
- `ingest`
- `apispec`
- `doctor` / `check`
- `validate-manifest` and `validate-metadata`
- `test-metrics`
- `refactor`
- database helpers (`webapp`, `serve`, `dbschema`)

Adding pages or sidebar entries for these commands would provide complete parity.
Where appropriate, terminology should mirror the CLI (e.g. “EDRR Cycle”) to avoid
confusion.

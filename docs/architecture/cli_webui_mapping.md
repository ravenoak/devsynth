---
author: DevSynth Team
date: '2025-06-19'
last_reviewed: "2025-08-03"
status: draft
tags:

- architecture
- ux
- cli
- webui
- dpg

title: CLI to WebUI and Dear PyGUI Command Mapping
version: 0.1.0
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; CLI to WebUI and Dear PyGUI Command Mapping
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; CLI to WebUI and Dear PyGUI Command Mapping
</div>

# CLI to WebUI and Dear PyGUI Command Mapping

The table below maps each DevSynth CLI command to the WebUI page or action and
the Dear PyGUI widget that execute the same workflow. `N/A` indicates that no
equivalent UI element is currently available. All interfaces use the `UXBridge`
abstraction to reuse the CLI's backend functions.

| CLI Command / Subcommand  | WebUI Page / Action                                   | Dear PyGUI Widget / Action               |
|---------------------------|-------------------------------------------------------|------------------------------------------|
| `init`                    | **Onboarding** – Initialize Project form             | **Init** button                           |
| `spec`                    | **Requirements** – Generate Specs form               | N/A                                      |
| `test`                    | **Synthesis** – Generate Tests form                  | N/A                                      |
| `code`                    | **Synthesis** – Generate Code button                 | N/A                                      |
| `run-pipeline`            | **Synthesis** – Run Pipeline button                  | N/A                                      |
| `config`                  | **Config** – Update/View Configuration               | N/A                                      |
| `config enable-feature`   | **Config** – Manage Feature Flags                    | N/A                                      |
| `inspect`                 | **Requirements** – Inspect Requirements form         | **Inspect** button                        |
| `gather`                  | **Requirements** – Requirements Plan Wizard          | **Gather** button                         |
| `wizard`                  | **Requirements** – Requirements Wizard               | N/A                                      |
| `inspect-code`            | **Analysis** – Inspect Code form                     | N/A                                      |
| `refactor`                | **Analysis** – Refactor Suggestions page             | N/A                                      |
| `webapp`                  | **Web App** – Web App Helper page                    | N/A                                      |
| `serve`                   | **Serve** – API Server management page               | N/A                                      |
| `dbschema`                | **Database** – Database Schema page                  | N/A                                      |
| `doctor` / `check`        | **Doctor** – Diagnostics page                        | N/A                                      |
| `EDRR-cycle`              | **EDRR** – Cycle execution page                      | N/A                                      |
| `align`                   | **Alignment** – SDLC consistency checks              | N/A                                      |
| `alignment-metrics`       | **Alignment Metrics** – Metrics reporting page       | N/A                                      |
| `inspect-config`          | **Inspect Config** – Configuration analysis page     | N/A                                      |
| `validate-manifest`       | **Validate Manifest** – Configuration validation page | N/A                                      |
| `validate-metadata`       | **Validate Metadata** – Metadata validation page     | N/A                                      |
| `test-metrics`            | **Test Metrics** – Test metrics reporting page       | N/A                                      |
| `generate-docs`           | **Generate Docs** – Documentation generation page    | N/A                                      |
| `ingest`                  | **Ingest** – Project ingestion page                  | N/A                                      |
| `apispec`                 | **API Spec** – API specification page                | N/A                                      |
| `webui`                   | Launches the WebUI                                   | N/A                                      |
| `dpg`                     | N/A                                                   | Launches the Dear PyGUI interface        |

All CLI commands now have corresponding WebUI pages. The Dear PyGUI desktop
client exposes buttons for common workflows. Each interface calls workflow
functions through the `UXBridge` layer, ensuring consistent behaviour between
the CLI and graphical front‑ends.

Because each interface invokes workflow functions through the `UXBridge`
layer, adding UI support for commands later only requires new widgets that
call the same shared functions.

Terminology across the CLI, WebUI, and Dear PyGUI is kept consistent. For
example, the interactive workflow started by `gather` is called the *Requirements
Plan Wizard* in all interfaces.

![Dear PyGUI layout](diagrams/dpg_overview.svg)
## Implementation Status

This mapping is **implemented** for all major WebUI workflows and the core
Dear PyGUI buttons. Several lesser‑used commands remain planned for future
releases, as noted in the table above.

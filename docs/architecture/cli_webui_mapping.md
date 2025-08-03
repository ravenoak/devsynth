---
author: DevSynth Team
date: '2025-06-19'
last_reviewed: "2025-07-10"
status: draft
tags:

- architecture
- ux
- cli
- webui

title: CLI to WebUI Command Mapping
version: 0.1.0
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; CLI to WebUI Command Mapping
</div>

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Architecture</a> &gt; CLI to WebUI Command Mapping
</div>

# CLI to WebUI Command Mapping

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
| `refactor`                | **Analysis** – Refactor Suggestions page             |
| `webapp`                  | **Web App** – Web App Helper page                    |
| `serve`                   | **Serve** – API Server management page               |
| `dbschema`                | **Database** – Database Schema page                  |
| `doctor` / `check`        | **Doctor** – Diagnostics page   |
| `EDRR-cycle`              | **EDRR** – Cycle execution page   |
| `align`                   | **Alignment** – SDLC consistency checks   |
| `alignment-metrics`       | **Alignment Metrics** – Metrics reporting page        |
| `inspect-config`          | **Inspect Config** – Configuration analysis page     |
| `validate-manifest`       | **Validate Manifest** – Configuration validation page|
| `validate-metadata`       | **Validate Metadata** – Metadata validation page     |
| `test-metrics`            | **Test Metrics** – Test metrics reporting page       |
| `generate-docs`           | **Generate Docs** – Documentation generation page    |
| `ingest`                  | **Ingest** – Project ingestion page                  |
| `apispec`                 | **API Spec** – API specification page                |
| `webui`                   | Launches the WebUI                                   |

All CLI commands now have corresponding WebUI pages. Each page calls workflow functions through the `UXBridge` layer, ensuring consistent behavior between the CLI and WebUI interfaces.

Because each page calls workflow functions through the `UXBridge` layer,
adding UI support for these commands later only requires new pages that
invoke the same shared functions.

Terminology across the CLI and WebUI is kept consistent. For example, the
interactive workflow started by `gather` is called the *Requirements Plan
Wizard* in both interfaces.
## Implementation Status

This mapping is **implemented** for all major workflows. Several
lesser-used commands remain planned for future releases, as noted in the
table above.

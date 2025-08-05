---
title: "DevSynth Release Plan"
date: "2025-08-20"
version: "0.1.0-alpha.1"
tags:
  - roadmap
  - release
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-20"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Roadmap</a> &gt; DevSynth Release Plan
</div>

# DevSynth Release Plan

This release plan defines version milestones for DevSynth starting with the upcoming `0.1.0-beta.1` pre-release and outlines the path toward the `0.1.x` line and future minor versions.

## Milestones

### 0.1.0-alpha.1

Before publishing the first alpha tag, ensure the artifacts build and the
project passes a quick smoke test:

```bash
task release:prep
git tag v0.1.0-alpha.1
git push origin v0.1.0-alpha.1
```

- MVUU JSON schema finalization
- Commit-message linter enforcement
- Traceability automation and ticket linkage
- Baseline Dear PyGui parity tasks:
  - Wizard forms
  - Progress UI
  - CLI mapping

### 0.1.0-beta.1
- Refresh system architecture diagrams under `docs/architecture/`.
- Standardize metadata headers across all project documentation.
- Publish the consolidated release plan for team-wide alignment.
- MVUU JSON schema finalization
- Commit-message linter enforcement
- Traceability automation and ticket linkage
- Baseline Dear PyGui parity tasks:
  - Wizard forms
  - Progress UI
  - CLI mapping

### 0.1.0
- Stabilize core agent APIs and complete critical test coverage.
- Finalize user-facing documentation, including updated WebUI instructions.
- Prepare packaging and automation for a tagged stable release.

### 0.2.0
- Achieve baseline Dear PyGui parity for core workflows via the desktop interface; requires the `gui` optional extras (`devsynth[gui]`). See the [Dear PyGui User Guide](../user_guides/dearpygui.md).
- Expand WebUI features with enhanced requirements workflows.
- Introduce plugin interfaces for third-party provider integration.
- Iterate on memory system scalability and performance.

### MVUU Dashboard
- Launch Streamlit MVUU traceability dashboard accessible via `devsynth mvuu-dashboard`.

### 0.2.0+
- Implement feature flags for experimental modules.
- Automate project-board synchronization with release milestones.
- Introduce a Jira adapter for issue tracking integration.

### 0.3.0
- Reach full feature parity with Dear PyGui across advanced workflows.
- Refine plugin architecture and cross-platform GUI support.

Future milestones will be appended to this document as they are defined. For implementation status of individual features, consult the [Feature Status Matrix](../implementation/feature_status_matrix.md).

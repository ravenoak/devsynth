---
title: "DevSynth Release Plan"
date: "2025-08-20"
version: "0.1.0a1"
tags:
  - roadmap
  - release
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-26"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Roadmap</a> &gt; DevSynth Release Plan
</div>

# DevSynth Release Plan

This release plan defines version milestones for DevSynth starting with the upcoming `0.1.0a1` pre-release and outlines the path toward the `0.1.x` line and future minor versions. For the actionable readiness checklist tied to this plan, see ../tasks.md.

## Milestones

### 0.1.0a1

Before publishing the first alpha tag, ensure the artifacts build and the
project passes a quick smoke test:

```bash
task release:prep
git tag v0.1.0a1
git push origin v0.1.0a1
```

- Refresh system architecture diagrams under `docs/architecture/`.
- Standardize metadata headers across all project documentation.
- Publish the consolidated release plan for team-wide alignment.
- MVUU engine prototype and refinement for Minimum Viable Utility Units.
- Atomic-Rewrite workflow baseline and integration.
- MVUU JSON schema finalization.
- Commit-linter enforcement.
- Traceability automation and ticket linkage.
- Automatic issue comments for commit traceability.
- Baseline Dear PyGui parity tasks:
  - Wizard forms
  - Progress UI
  - CLI mapping

#### Prerequisite Completion Status (0.1.0a1)

- [ ] Refresh system architecture diagrams under `docs/architecture/` (tracked under Documentation Quality gates)
- [x] Standardize metadata headers across all project documentation (front matter standardized for key sections)
- [x] Publish the consolidated release plan for team-wide alignment (this document, status: published)
- [ ] MVUU engine prototype and refinement for Minimum Viable Utility Units
- [ ] Atomic-Rewrite workflow baseline and integration
- [ ] MVUU JSON schema finalization
- [ ] Commit-linter enforcement
- [ ] Traceability automation and ticket linkage
- [ ] Automatic issue comments for commit traceability
- [ ] Baseline Dear PyGui parity tasks:
  - [ ] Wizard forms
  - [ ] Progress UI
  - [ ] CLI mapping

### 0.1.0a2 (Planned)
- Carry over deferred items from 0.1.0a1 that did not block the tag.
- CI/CD matrix hardening (minimal/full/docs/lint/type jobs) and artifacts publication.
- Provider system safe defaults fully validated with integration tests using local stubs.
- Release management updates: README badges/links, metadata verification automation.

### 0.1.0
- Stabilize core agent APIs and complete critical test coverage.
- Finalize user-facing documentation, including updated WebUI instructions.
- Prepare packaging and automation for a tagged stable release.
- Finalize MVUU engine and Atomic-Rewrite tooling.
- Complete MVUU dashboard for requirements traceability via `devsynth mvuu-dashboard`.

### 0.1.1
- Achieve baseline Dear PyGui parity for core workflows via the desktop interface; requires the `gui` optional extras (`devsynth[gui]`). See the [Dear PyGui User Guide](../user_guides/dearpygui.md).
- Expand WebUI features with enhanced requirements workflows.
- Introduce plugin interfaces for third-party provider integration.
- Iterate on memory system scalability and performance.

### MVUU Dashboard (Completed)
NiceGUI MVUU traceability dashboard accessible via `devsynth mvuu-dashboard`.

### 0.1.1+ (Future Features)
- Implement feature flags for experimental modules.
- Introduce feature flags for the MVUU dashboard and Dear PyGui interface.
- Automate project-board synchronization with release milestones.
- Introduce a Jira adapter for issue tracking integration.

### 0.3.0
- Reach full feature parity with Dear PyGui across advanced workflows.
- Refine plugin architecture and cross-platform GUI support.

Future milestones will be appended to this document as they are defined. For implementation status of individual features, consult the [Feature Status Matrix](../implementation/feature_status_matrix.md).

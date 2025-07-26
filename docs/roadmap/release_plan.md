---
title: "DevSynth Release Plan"
date: "2025-07-07"
version: "0.1.0"
tags:
  - "roadmap"
  - "release"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-20"
---

# DevSynth Release Plan

This document consolidates the various roadmap drafts into a single authoritative plan. **It is the canonical source for all roadmap updates.** It outlines the major phases leading to a stable 1.0 release and summarizes key version milestones.

DevSynth remains in a pre-release stage. No official release has been published yet and versions in this plan are provisional. They follow the MAJOR.MINOR.PATCH-STABILITY notation defined in our [Semantic Versioning+ policy](../policies/semantic_versioning.md).
Dependencies among major features are summarized in [Feature Dependencies](feature_dependencies.md) to clarify how releases build on each other.

## Phased Roadmap

1. **Foundation Stabilization** (0.1.x – Q1 2025)
   - Finalize core architecture (EDRR, WSDE, providers, memory).
   - Anthropic and deterministic offline providers are fully implemented.
   - Address adoption barriers and ensure offline capabilities.
   - Establish baseline testing and documentation.
   - Phase 1 is largely complete; remaining tasks include finalizing the WSDE
     peer review workflow and resolving outstanding test failures. See the
     [Feature Status Matrix](../implementation/feature_status_matrix.md) for
     detailed progress on collaboration features.

2. **Production Readiness** (0.2.x–0.3.x – Q2 2025)
   - Polish CLI UX and integrate the initial Web UI.
   - Perform repository analysis and improve code organization.
   - Expand automated testing and CI/CD.
   - Introduce multi-language code generation starting in **0.2.x**. See [Post-MVP Roadmap](post_mvp_roadmap.md#phase-4-advanced-code-generation-and-refactoring) for details.
   - Provide AST mutation tooling for automated refactoring and testing in **0.3.x** (refer to [Post-MVP Roadmap](post_mvp_roadmap.md#phase-3-self-improvement-capabilities)).

3. **Collaboration & Validation** (0.4.x–0.6.x – Q3–Q4 2025)
   - Enhance multi-agent collaboration features.
   - Validate workflows with real-world projects and community feedback.
   - Iterate on metrics, analytics, and documentation quality.
   - Integrate the experimental DSPy-AI framework in **0.6.x**. More information is available in [Post-MVP Roadmap](post_mvp_roadmap.md#phase-6-dspy-ai-integration).

4. **Full Release & Innovation** (0.7.x–1.0.0 – 2026)
   - Harden security and performance for production deployments.
   - Complete Web UI and API features.
   - Finalize documentation and publish the 1.0 release.
   - Plan post-1.0 innovations and enterprise capabilities.
   - Apply Promise-Theory reliability enhancements beginning in **0.7.x** with stabilization by **0.9.0** (see [Post-MVP Roadmap](post_mvp_roadmap.md#phase-7-promise-theory-reliability-enhancements)).

### Version Milestones

- **0.1.0-alpha.1**: Core architecture in place with Anthropic and offline
  providers, baseline CLI commands, and initial EDRR/WSDE integration.
- **0.1.0-beta.1**: WSDE peer review workflow targeted for completion
  (see [issue 104](../../issues/104.md)), Web UI preview available, and major
  tests passing.
- **0.1.0-rc.1**: Documentation freeze and full test suite passing as the
  release candidate for version 0.1.0.
- **0.2.0–0.6.0**: Incremental releases adding collaboration, Web UI, and testing improvements.
- **0.2.x**: Multi-language code generation support.
- **0.3.x**: AST mutation tooling for refactoring.
- **0.6.x**: Experimental DSPy-AI integration (finalize by **0.8.0**).
- **0.7.x–0.9.0**: Optimization, Promise-Theory reliability work, and preparation for the 1.0 release.
- **1.0.0**: Stable release with comprehensive documentation and production readiness.

This plan supersedes the individual phase tables previously scattered across multiple documents. All future roadmap updates should occur here.

For a detailed breakdown of feature implementation progress, see the
[Feature Status Matrix](../implementation/feature_status_matrix.md).

## Implementation Status
Execution of this release plan is **in progress** with milestones tracked in [issue 104](../../issues/104.md). The repository harmonization effort has concluded, the **0.1.0-alpha.1** milestone is complete, and preparations for `0.1.0-beta.1` are underway.

### Current Test Summary

Recent CI reports collected **2547** tests but aborted during collection with **1 error** (ModuleNotFoundError for `chromadb_store`). **15** tests were skipped. See the [development status](development_status.md#test-failure-summary) document for details.
To publish `0.1.0-beta.1`, the project must:

- Resolve the outstanding WebUI and EDRR coordinator test failures.
- Finish the WSDE peer review workflow and solidify memory initialization.
- Address remaining partial features listed in the
  [Feature Status Matrix](../implementation/feature_status_matrix.md) such as
  Methodology Integration and the Retry Mechanism.
- Continue documentation cleanup and polish the Web UI preview.

---

title: DevSynth Roadmap
date: '2025-07-07'
last_reviewed: '2025-07-20'
tags:
  - roadmap
  - milestones
version: "0.1.0a1"
status: published
author: DevSynth Team
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Archived &gt; Roadmaps &gt; DevSynth Roadmap
</div>

# DevSynth Roadmap

**Note:** DevSynth is currently in a pre-release stage. Refer to the [Release Plan](release_plan.md) for canonical milestones.

This document provides a simplified overview of upcoming release milestones. For
full details, see the [Release Plan](release_plan.md). Current feature progress
is summarized in the [Feature Status Matrix](../implementation/feature_status_matrix.md).
A comprehensive plan for Phase 2 implementation is available in the [Task Progress](../../TASK_PROGRESS.md) document.

- **Pre-0.1.0** – Internal iterations and prototype development. No package is published yet.
- **0.1.0-alpha.1** – Core architecture completed with offline provider support, baseline CLI commands, and initial tests (~50% coverage).
- **0.1.0-alpha.1** – Peer review workflow and Web UI preview with major tests passing and coverage ≥75%.
- **0.1.0-rc.1** – Documentation freeze and full test suite passing with coverage ≥90%.
- **0.1.x** – Expanded agent capabilities, improved memory backends, and API enhancements.
- **1.0.0** – First stable release with comprehensive documentation and deployment automation.

## Current Release Status

DevSynth has completed the **0.1.0-alpha.1** milestone which finalized the core architecture, added offline provider support, and delivered baseline CLI commands with around **50%** coverage.

The project is now preparing the **0.1.0-alpha.1** release, introducing the peer review workflow and a Web UI preview while pushing coverage to **≥75%**. The subsequent **0.1.0-rc.1** milestone represents a documentation freeze with the full test suite passing and coverage **≥90%** in accordance with our [Testing Standards](../developer_guides/TESTING_STANDARDS.md). Detailed implementation progress for these milestones is available in the [Feature Status Matrix](../implementation/feature_status_matrix.md).

### Completed Phase 1 Tasks

The Foundation Stabilization phase finished with the following accomplishments:

- Deployment automation via multi-stage Docker builds and Docker Compose
- Environment-specific configuration with validation scripts
- Documentation updates, including the comprehensive Deployment Guide


## Implementation Status

The roadmap is actively maintained. After the feature audit
approximately **60%** of the planned functionality is available.
Major milestones remain in progress as documented in the
[Feature Status Matrix](../implementation/feature_status_matrix.md).

## Current Limitations

- Release dates are tentative and depend on resolving failing tests.
- Deployment automation requires further work.

---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: '2025-07-07'
status: published
tags:
- release-plan
- roadmap
title: DevSynth Pre-1.0 Release Plan
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; Archived &gt; Roadmaps &gt; DevSynth Pre-1.0 Release Plan
</div>

# DevSynth Pre-1.0 Release Plan

**Note:** DevSynth is still in pre-release. Current versions are in the `0.1.x`
series while this document outlines the path toward an eventual 1.0 release.
**No version has been officially released yet.**

For the authoritative roadmap, see the [Release Plan](release_plan.md).

We propose a multi-phase plan to finalize DevSynth’s UX, architecture, and completeness.  Each phase defines targeted milestones and implementation-ready tasks, emphasizing BDD/TDD practices.  We draw on the current codebase and docs to identify missing features and gaps.

For current implementation status, see the
[Feature Status Matrix](../implementation/feature_status_matrix.md).

## Provider Completion Summary

DevSynth now includes a fully implemented Anthropic provider along with a
deterministic offline provider. The Anthropic integration supports API
configuration and streaming completions. The offline provider enables
repeatable text and embeddings when `offline_mode` is enabled, ensuring all
workflows operate without network access.

## Phase 1: Core Architecture & Foundation Stabilization

**Goals:** Finalize architectural components (EDRR, WSDE, providers, memory), resolve tech debt, and ensure code structure and config standards.

* **Audit & Gap Analysis:** Per the [Feature Status Matrix](../implementation/feature_status_matrix.md), the Anthropic provider, offline mode, and WSDE peer review are implemented. Remaining gaps focus on finalizing EDRR tooling and memory store integration.

* **UXBridge & Hexagonal Layers:** Ensure all interfaces (CLI, WebUI, Agent API) use the common **UXBridge** abstraction.  This confirms the hexagonal architecture: core workflows are UI-agnostic and testable.  *(Task: write unit tests for `UXBridge.ask_question`/`display_result` to guarantee consistent behavior across CLI and future UI.)*

* **Configuration & Requirements:** Confirm Python 3.12+ support (per [README]) and update `pyproject.toml`, `.devsynth/project.yaml` schema, and default config.  Document any constraints (e.g. optional vector DBs).
* **Offline Mode (Implemented):** The offline provider supplies deterministic text and embeddings when `offline_mode` is enabled. CLI and WebUI fallbacks are verified with unit tests for provider selection. See the [Feature Status Matrix](../implementation/feature_status_matrix.md) for status details.
* **Optional Vector Stores:** Provide configuration examples for alternative memory stores like **ChromaDB** in addition to Kuzu, FAISS, and LMDB. The configuration loader now recognizes `memory_backend: chromadb` and `docker-compose.yml` ships with a sample `chromadb` service.

With these items and the WSDE peer review implementation confirmed in the [Feature Status Matrix](../implementation/feature_status_matrix.md), Phase 1 is nearly finished. Remaining work involves integrating the ChromaDB adapter and resolving the outstanding test failures noted in the development status reports.

* **Pseudocode & BDD Examples:** Draft pseudocode for core routines, e.g.:

  ```python
  # Pseudocode: high-level workflow orchestration (EDS: Expand/Differentiate/Synthesize)
  task = load_task()
  cycle = EDRRCoordinator(memory, team, analyzer, transformer, prompts, docs)
  cycle.start_cycle(task)  # initiates Expand->Differentiate->Refine...
  result = team.delegate_task(task)  # WSDE consensus/dialectical
  ```

  *Example Gherkin (feature file)*:

  ```gherkin
  Feature: Project Initialization Wizard
    As a user, I can initialize a DevSynth project with guided prompts.
    Scenario: Initialize new project
      Given no DevSynth project exists at path "myproj"
      When I run `devsynth init` and answer setup questions
      Then a `.devsynth/project.yaml` is created with my inputs
      And `devsynth config` shows the selected feature flags
  ```

  *(Step definitions would call `init_cmd` and assert file outputs.)*

* **Missing Modules & Refactoring:** Identify any unused or commented-out code (e.g. specialized agent classes in `agent_adapter.py`).  Remove dead code or implement missing pieces (e.g. if we want separate Planner/Test/Code agents).  Address technical debt in logic (e.g. simplify overly complex methods, ensure logging consistency).

* **Tests:** Write unit tests for all core modules.  For example, test `WSDETeam.assign_roles`, `select_primus_by_expertise`, `build_consensus`, etc.  *Coverage goal:* ≥80% lines in core modules (EDRR, WSDE, memory, LLM provider, code analysis).

## Phase 2: CLI UX Polishing & Web UI Integration

**Goals:** Complete and polish the CLI user experience, and build a preliminary Web UI leveraging the CLI logic.

* **CLI Commands:** Ensure all CLI flows work end-to-end and are tested.  Key commands include `init`, `spec`, `test`, `code`, `run-pipeline`, `config`, `gather`, `refactor`, `inspect`, `webapp`, `serve`, `dbschema`.  For each:

  * **UX Specifications/User Stories:**

    * *Init:* “As a developer, I can run `devsynth init` to configure a new or existing project.”
    * *Spec/Test/Code:* “Given requirements/specs, DevSynth generates specs/tests/code.”
    * *Doctor/Check:* “As a user, I can run `devsynth doctor` to validate my environment (Python version, API keys).”
    * *Config:* “I can view and set config (e.g. model selection).”
    * *Refactor:* “DevSynth suggests next steps via `devsynth refactor`.”
    * *Inspect:* “I can interactively parse `requirements.txt`.”
    * *Webapp:* “I can scaffold a sample web app (`flask`, etc) easily.”
    * *Serve:* “I can launch the DevSynth API server (`uvicorn`) for integrations.”
  * **BDD / Gherkin Tests:** For each story, write scenarios.  Example for `spec`:

    ```gherkin
    Feature: Specification Generation
      Scenario: Generate specs from requirements
        Given a `requirements.md` file with user stories
        When I run `devsynth spec --requirements-file requirements.md`
        Then a `specs.md` file is created with generated specifications
        And the CLI outputs a success message
    ```

    *(Implement step defs that invoke `spec_cmd` and verify file output.)*
  * **UX Flow Diagrams:** Document CLI flowcharts, e.g.:

    ```json
    [User Input] --devsynth init--> [init_cmd prompts] --> [init_project executes] --> [Write project.yaml] --> [Feature flags toggled]
    ```

    (Refer to the UXBridge diagram for shared flow.)
  * **CLI Improvements:** Add any missing prompts or validations.  E.g. the `doctor` command (from key features) should check services (like `_check_services` does) and be accessible via CLI.  Write tests for the `doctor_cmd` (e.g. missing API keys triggers a warning).


* **Web UI (NiceGUI) Integration:** Based on the **WebUI Architecture** spec:

  * Implement a `WebUI` class that inherits `UXBridge`, using NiceGUI pages (“Onboarding”, “Requirements”, “Analysis”, “Synthesis”, “Config”) as outlined.  Each page should call the same CLI workflows under the hood.
  * **Pseudocode** (in docs) shows the navigation logic; code tasks include wiring up each page (calling `init_cmd`, `gather_cmd`, etc.).  *BDD example:*

    ```gherkin
    Feature: WebUI Navigation
      Scenario: Access project onboarding page
        When I select "Onboarding" in the sidebar
        Then the Onboarding UI appears
        And the same prompts from `devsynth init` are displayed
    ```

    *(Step defs would simulate NiceGUI UI selection and assert pages call underlying workflows.)*
  * **Agent Interface:** Ensure the Agent API endpoints (per `agentapi.py`) are fully implemented and tested: `/init`, `/gather`, `/synthesize`, `/status`.  For example, write an integration test that calls `POST /init` and checks that `LATEST_MESSAGES` reflects the `init_cmd` output.  *User story:* “As an external agent, I can invoke DevSynth workflows via HTTP.”
  * **Bridging CLI and WebUI:** Use the same `UXBridge` for both interfaces.  Tests should verify that both CLI commands and HTTP API produce identical effects (e.g. project files) when given the same input.

## Phase 3: Multi-Agent Collaboration & EDRR Enhancements

**Goals:** Complete team collaboration features and ensure the adaptive EDRR pipeline is fully integrated.

* **WSDE Model:** Finalize non-hierarchical collaboration.  The **WSDETeam** and **WSDETeamCoordinator** already support rotating primus, consensus voting, and dialectical hooks.  Tasks:

  * Verify and test *peer-based* behavior: write BDD for scenarios like “creating multiple agents leads to peer roles”, “rotating Primus works”.
  * Ensure `delegate_task` (in `WSDETeamCoordinator`) aggregates solutions and builds consensus/dialectical analysis.  *Example test:* mock multiple `UnifiedAgent.process` calls and assert that `delegate_task`’s output includes all contributors and a `method: consensus_synthesis` (as in the BDD steps).
  * Implement or fix any missing logic: e.g. `vote_on_critical_decision`, peer review cycles.  The [Feature Status Matrix](../implementation/feature_status_matrix.md) shows the peer review mechanism is implemented, but the full workflow still needs completion.  Finish peer-review workflow (e.g. integrate `PeerReview` class, test it end-to-end).
  * **Context-Driven Leadership:** Ensure `select_primus_by_expertise` works as intended (as per tests).  Write unit tests for tasks switching Primus roles.
  * **DSL & EDRR Integration:** The EDRRCoordinator orchestrates expand/differentiate/refine cycles. Complete its CLI integration: e.g. an `edrr-cycle` command to step through phases (see `edrr_cycle_cmd` imported in CLI).  Test a full EDRR run on a sample task, verifying that source code is analyzed and artifacts stored in memory.
  * **Test Goals:** Achieve complete behavior-driven coverage for collaboration: every Gherkin scenario in `tests/behavior` should pass.  Add missing scenarios (e.g. dialectical reasoning, retrospection) and step definitions.

## Phase 4: Testing, Documentation & Final Polish

**Goals:** Attain high test coverage, finalize all documentation, and polish UX details.

* **Test Coverage:** Target ≥90% for unit tests in critical modules (especially core and UX bridges).  Add integration tests for CLI/WebUI/AgentAPI pipelines.  Cover corner cases (invalid config, missing files).  Automate coverage checks in CI.
* **Behavior Tests:** Complete feature files for any remaining user stories (e.g. `Feature: Generate documentation`, `Feature: Web Application Generator`).  Implement step definitions in Python to drive these flows via `CLIUXBridge` or `APIBridge`.
* **Documentation:** Ensure **all** features and workflows are documented: update **User Guide**, **Quick Start**, **CLI Reference**, and **Architecture** docs.  In particular, document new features (WebUI, API endpoints, agent workflows).  Verify docs match code via traceability matrix.  Add missing images or diagrams to docs.
* **UX Polish:** Refine command-line messaging (colors, formatting), fix any inconsistent naming.  E.g. confirm that all commands have help text.  Ensure CLI patterns are consistent.
* **Alignment Metrics:** Integrate the `alignment_metrics` command and WebUI page.  Provide sample reports showing traceability between requirements, specs, tests, and code.  Include BDD scenarios for generating alignment metrics.
* **Test Metrics:** Integrate the `test_metrics` command to analyze test-first development patterns and coverage.

See [Release Plan](release_plan.md) for the consolidated roadmap and version milestones.
## Implementation Status

This pre-1.0 plan is **in progress**. Outstanding tasks are tracked in
[issue 102](../../issues/archived/CLI-and-UI-improvements.md).

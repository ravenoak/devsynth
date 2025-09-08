---
adr: 0001
status: accepted
date: 2025-08-26
title: Testing Strategy and Speed Marker Policy
authors:
  - DevSynth Team
links:
  - ../overview.md
  - ../../developer_guides/testing.md
  - ../../../scripts/verify_test_markers.py
  - ../../../project guidelines
---

# ADR-0001: Testing Strategy and Speed Marker Policy

Context
- DevSynth enforces deterministic, offline-first testing with strong isolation. Tests are segmented by speed to support targeted execution in CI and local workflows.
- A strict policy requires exactly one speed marker per test function: @pytest.mark.fast | @pytest.mark.medium | @pytest.mark.slow. Module-level substitutes are not allowed for speed categories.
- scripts/verify_test_markers.py is the canonical validator; CI must surface a machine-readable report (test_markers_report.json) to prevent regressions and aid triage.

Decision
- Adopt and enforce a repository-wide Speed Marker Policy:
  - Exactly one of fast/medium/slow at the function level for every test function.
  - Additional markers (e.g., @pytest.mark.property, @pytest.mark.requires_resource("<NAME>")) may be present but do not substitute speed markers.
  - Property-based tests (opt-in) must include both @pytest.mark.property and a speed marker.
- Integrate a CI job that runs scripts/verify_test_markers.py --report and publishes test_markers_report.json as an artifact on PRs and pushes to main.
- Align testing strategy with project guidelines and docs/plan.md principles: offline-first, isolation by default, and clear CLI ergonomics via devsynth run-tests.

Rationale (Dialectical)
- Thesis: Flexible marker usage reduces contributor friction.
- Antithesis: Non-uniform markers undermine CI segmentation and create ambiguity; module-level markers hide violations.
- Synthesis: Enforce exactly one explicit speed marker per function, automated by a verifier and backed by CI reporting, while allowing orthogonal markers for opt-in behaviors and resources.

Consequences
- Pros:
  - Predictable CI segmentation and stable execution time characteristics.
  - Clear contributor guidance and automated feedback loops via CI.
  - Easier flakiness triage and performance budgeting.
- Cons:
  - Initial effort to fix legacy violations and maintain discipline.
  - Slight overhead for contributors to remember the policy.

Implementation Notes
- Use Poetry to run the verifier consistently: poetry run python scripts/verify_test_markers.py --report --report-file test_markers_report.json
- Property testing is gated by DEVSYNTH_PROPERTY_TESTING=true; see docs/ developer_guides/testing.md for conventions.
- Resource-gated tests rely on @pytest.mark.requires_resource and env flags (DEVSYNTH_RESOURCE_*); defaults are set in tests/conftest.py.

Status and Follow-up
- Status: accepted and implemented via a dedicated CI workflow that generates and uploads the markers report.
- Future work: extend CI to comment summary statistics on PRs; integrate with test inventory caching; add unit tests asserting verifier error categories.

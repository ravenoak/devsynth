# ADR-001: BDD Speed Marking — Definition-time vs Collection-time

Status: Accepted
Date: 2025-09-04

Context
- The repository enforces exactly one speed marker per test function (@pytest.mark.fast|medium|slow).
- pytest-bdd generates scenario wrapper functions at collection time, which may lack explicit speed marks in source, leading to PytestWarnings.
- We currently auto-inject a default speed marker for behavior tests during pytest_collection_modifyitems in tests/conftest.py, scoped to tests/behavior/ to avoid interfering with unit/integration tests.

Decision
- Stick with collection-time auto-injection for 0.1.0a1. Do not implement definition-time decorators or plugins pre-release.
- Keep a targeted filterwarnings in pytest.ini to ignore only the specific pytest-bdd speed-marker PytestWarning. Do not globally disable warnings.

Rationale
- Minimal surface-area change: no need to modify many generated scenario functions.
- Easily reversible and observable in one place (tests/conftest.py), aligning with our smoke and gating behavior.
- Definition-time plugins risk import-order and plugin dependency issues; defer to post-release evaluation.

Consequences
- Behavior tests without explicit speed marks will be marked @pytest.mark.fast by default at collection.
- Static marker verification remains source-based; we added cross-checking options in scripts/verify_test_markers.py to align source and collected inventory.

Alternatives considered
- Definition-time decorator/plugin to wrap pytest-bdd scenario creation to attach marks: more intrusive; postponed.
- Forcing explicit marks in all behavior test sources: higher churn; useful as a longer-term hygiene goal.

References
- Plan: docs/plan.md (Track A A1–A1c)
- Harness: tests/conftest.py (pytest_collection_modifyitems)
- pytest.ini filterwarnings

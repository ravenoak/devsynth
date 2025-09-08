# Unit Test Suite Triage

Purpose: Provide a current inventory of unit test failures, categorize by module, and create actionable sub-issues per module. This document is maintained iteratively and supports SDD/TDD/BDD alignment per project guidelines.

Updated: 2025-08-24
Owner: QA/DevInfra

## How to Reproduce (local minimal)

- Minimal dependencies:
  - poetry install --with dev --extras minimal
  - poetry run pytest -q tests/unit

Optional: For full extras
- poetry install --all-extras --all-groups
- poetry run pytest -q tests/unit

## Inventory

Record failures with brief context; link to sub-issues below.

- [ ] Module: application/requirements
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/unit/application/requirements -k failing_test
  - Linked issue: issues/triage/unit_application_requirements.md
- [ ] Module: application/orchestration
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/unit/application/orchestration
  - Linked issue: issues/triage/unit_application_orchestration.md
- [ ] Module: application/memory
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/unit/application/memory
  - Linked issue: issues/triage/unit_application_memory.md
- [ ] Module: adapters/llm
  - Symptoms: TBD
  - Repro: poetry run pytest -q tests/unit/adapters/llm
  - Linked issue: issues/triage/unit_adapters_llm.md

Add more modules as needed.

## Sub-Issues

Create one file per module under issues/triage/ and link from the inventory. Each sub-issue should include:
- Summary of failures
- Root cause hypothesis (dialectical: thesis/antithesis/synthesis)
- Proposed fix and tests (TDD)
- Acceptance criteria (BDD Given/When/Then)
- Impact/risk

Placeholders created:
- issues/triage/unit_application_requirements.md
- issues/triage/unit_application_orchestration.md
- issues/triage/unit_application_memory.md
- issues/triage/unit_adapters_llm.md

## Notes

- Keep deterministic seeds configured via tests/conftest.py where relevant.
- Avoid live network calls; use stubs/mocks by default.
- Align with docs/roadmap/release_plan.md and provider safety defaults.

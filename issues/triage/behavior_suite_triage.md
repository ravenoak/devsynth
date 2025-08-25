# Behavior-Driven (BDD) Test Suite Triage

Purpose: Inventory BDD failures, map to feature files and step definitions, and create actionable sub-issues. Maintained per .junie/guidelines.md and BDD best practices.

Updated: 2025-08-24
Owner: QA/DevInfra

## How to Reproduce

- Minimal dependencies (fast):
  - poetry install --with dev --extras minimal
  - poetry run pytest -q tests/behavior

- Full extras (when needed):
  - poetry install --all-extras --all-groups
  - poetry run pytest -q tests/behavior

## Inventory by Feature Area

- [ ] EDRR Coordinator
  - Feature files: tests/behavior/features/edrr_coordinator.feature, ...
  - Repro: poetry run pytest -q tests/behavior -k edrr_coordinator
  - Linked issue: issues/triage/bdd_edrr_coordinator.md
- [ ] Requirements Processing & Dialectical Reasoning
  - Features: tests/behavior/features/requirements/*.feature
  - Repro: poetry run pytest -q tests/behavior -k requirements
  - Linked issue: issues/triage/bdd_requirements_reasoning.md
- [ ] Collaboration & Orchestration
  - Features: tests/behavior/features/general/*.feature
  - Repro: poetry run pytest -q tests/behavior -k orchestration
  - Linked issue: issues/triage/bdd_collaboration_orchestration.md

## Sub-Issues

- issues/triage/bdd_edrr_coordinator.md
- issues/triage/bdd_requirements_reasoning.md
- issues/triage/bdd_collaboration_orchestration.md

## Notes

- Keep step definitions decoupled and deterministic; avoid provider calls in BDD by default.
- Ensure step fixtures honor seed settings; document Given/When/Then clearly with acceptance criteria.

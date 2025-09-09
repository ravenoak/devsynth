# BDD: EDRR Coordinator — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures from edrr_coordinator features; map to step definitions.

## Reproduction
poetry run pytest -q tests/behavior -k edrr_coordinator

## Acceptance Criteria (BDD)
Given EDRR coordinator BDD scenarios
When executed with minimal extras
Then step definitions align with EDRR phase transitions and all steps pass deterministically.

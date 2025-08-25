# BDD: Requirements Processing & Dialectical Reasoning — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures from requirements-related features; verify determinism across seeds.

## Reproduction
poetry run pytest -q tests/behavior -k requirements

## Acceptance Criteria (BDD)
Given requirements and dialectical reasoning BDD scenarios
When executed with a fixed seed via fixtures
Then outcomes (thesis/antithesis/synthesis) are deterministic and tests pass.

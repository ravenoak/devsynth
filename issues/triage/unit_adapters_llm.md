# Unit: adapters/llm — Triage

Status: Open
Updated: 2025-08-24

## Summary
TBD — Collect failures from tests/unit/adapters/llm.

## Thesis / Antithesis / Synthesis
- Thesis: TBD
- Antithesis: TBD
- Synthesis: TBD

## Proposed Fix
- Steps: TBD
- Tests: Use deterministic provider stubs; ensure safe defaults without API keys.

## Acceptance Criteria (BDD)
Given LLM adapter unit tests
When run without API keys and with stubs enabled
Then all tests avoid network calls and pass deterministically.

## Impact / Risk
Low; focused on provider abstractions.

---
author: DevSynth Team
date: "2025-08-26"
status: living
version: "0.1.0a1"
---
# Known Flakes Quarantine List

This living document tracks currently known flaky tests. Each entry must include a reproducible path, owner, and mitigation plan. Aligns with project guidelines and docs/plan.md.

Columns:
- Test node (file::test_name[param])
- Speed
- Target (unit/integration/behavior)
- Repro steps (exact command, env flags)
- Hypothesis (thesis) / Counter (antithesis) / Resolution (synthesis)
- Owner
- Status

Examples:

- tests/unit/some_module/test_cache.py::test_eviction_order [fast]
  - Target: unit
  - Repro:
    - poetry install --with dev --extras "tests"
    - DEVSYNTH_TEST_TIMEOUT_SECONDS=30 poetry run devsynth run-tests --speed=fast -k test_eviction_order --no-parallel
  - Notes (T/A/S):
    - Thesis: nondeterministic ordering due to set iteration.
    - Antithesis: ordering stabilized under PYTHONHASHSEED.
    - Synthesis: sort keys before comparison; add deterministic_seed fixture usage.
  - Owner: @maintainer
  - Status: Mitigation merged; monitoring

- tests/integration/test_network_paths.py::test_offline_isolation [fast]
  - Target: integration
  - Repro:
    - poetry install --with dev --extras "tests"
    - poetry run devsynth run-tests --smoke --speed=fast -k test_offline_isolation --no-parallel
  - Notes (T/A/S):
    - Thesis: httpx slipped past disable_network.
    - Antithesis: only websocket path leaked.
    - Synthesis: extended disable_network to cover websockets; added unit guard.
  - Owner: @maintainer
  - Status: Fixed

Maintenance:
- Update entries when flakes are reproduced or resolved.
- Move resolved items to the bottom with a “Resolved” status and link to the fixing PR.

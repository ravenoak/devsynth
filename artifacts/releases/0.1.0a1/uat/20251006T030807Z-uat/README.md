# UAT Evidence Bundle (v0.1.0a1)

- **Bundle ID**: `uat-20251006T030807Z`
- **Created**: 2025-10-06T03:08:07Z (UTC)
- **Scope**: Smoke verification, coverage manifest, strict typing manifest, release readiness snapshot

## Contents

| Component | Path | Notes |
| --- | --- | --- |
| Smoke log | `smoke/devsynth_run-tests_smoke_fast_20251004T201351Z.log` | Captures the latest smoke rerun recorded after MemoryStore protocol fixes; referenced by `issues/release-finalization-uat.md` for UAT sign-off. |
| Coverage manifest | `coverage/coverage_manifest_20251012T164512Z.json` | 92.40 % fast+medium aggregate with QualityGate/TestRun/ReleaseEvidence identifiers. |
| Strict typing log | `typing/mypy_strict_20251005T035128Z.log` (+ companion inventories) | Records the strict typing gate with knowledge-graph publication IDs. |
| Release readiness issue snapshot | `readiness/release-readiness-assessment-v0-1-0a1.md` | Captured alongside bundle creation to preserve the state referenced during UAT closure. |

The checksums for each artifact are documented in `bundle_manifest.json`.

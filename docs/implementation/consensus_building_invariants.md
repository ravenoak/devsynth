---
author: DevSynth Team
date: '2025-09-14'
last_reviewed: "2025-09-21"
status: review/published
tags:
- implementation
- invariants
title: Consensus Building Invariants
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Implementation</a> &gt; Consensus Building Invariants
</div>

# Consensus Building Invariants

The consensus utility provides deterministic majority voting over a finite
sequence of options. The algorithm counts votes once and derives a result
without iteration beyond that traversal.

## Majority Yields Stable Decisions

`build_consensus` selects the option with the highest count. When the
winning option meets the threshold, the function returns it as the
``decision`` and marks ``consensus`` true.

```python
from devsynth.consensus import build_consensus

result = build_consensus(["a", "a", "b"])
assert result.consensus and result.decision == "a"
```

## Dissent Tracking When Threshold Fails

If no option satisfies the threshold the result lists dissenting options
and the decision is ``None``.

```python
from devsynth.consensus import build_consensus

result = build_consensus(["a", "b"], threshold=0.6)
assert not result.consensus and set(result.dissenting) == {"a", "b"}
```

Regression coverage in
[`tests/unit/devsynth/test_consensus.py::test_build_consensus_tracks_unique_dissenting_options`](../tests/unit/devsynth/test_consensus.py)
ensures each dissenting option appears once when consensus fails, matching the
tracked counts and preventing stale entries from earlier runs.

These invariants guarantee termination and predictable outcomes for
finite inputs.

## Quantitative Proof Requirements

`docs/plan.md` requires executable proofs paired with coverage evidence before
consensus invariants may claim release readiness. The next coverage sweep must
record line coverage for `src/devsynth/consensus.py` alongside the updated test
artifacts so the measurement can be archived in
`issues/coverage-below-threshold.md` for traceability.【F:docs/plan.md†L194-L199】【F:issues/coverage-below-threshold.md†L86-L106】

## References

- Specification: [docs/specifications/consensus-building.md](../specifications/consensus-building.md)
- BDD Feature: [tests/behavior/features/consensus_building.feature](../tests/behavior/features/consensus_building.feature)
- Issue: [issues/consensus-building.md](../issues/consensus-building.md)
- Unit Tests: [tests/unit/devsynth/test_consensus.py](../tests/unit/devsynth/test_consensus.py)

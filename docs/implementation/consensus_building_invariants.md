---
author: DevSynth Team
date: '2025-09-14'
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

Regression coverage keeps this invariant stable. The fast unit test
`tests/unit/devsynth/test_consensus.py::test_build_consensus_no_consensus`
protects the two-vote example above, while
`tests/unit/devsynth/test_consensus.py::test_build_consensus_records_unique_dissenting_options`
confirms the dissenting roster enumerates each option once even when votes
arrive with duplicates, preserving deterministic audit trails for
downstream consumers.【F:tests/unit/devsynth/test_consensus.py†L10-L48】

These invariants guarantee termination and predictable outcomes for
finite inputs.

## Quantitative Proof Obligations

The test readiness plan still requires executable proofs accompanied by
coverage evidence before UAT can rely on these guarantees. A focused
coverage sweep of `devsynth.consensus` remains scheduled once the
instrumented `devsynth run-tests` workflow is restored so that the
consensus invariants contribute quantifiable line coverage, closing the
plan's outstanding measurement requirement.【F:docs/plan.md†L191-L197】

## References

- Specification: [docs/specifications/consensus-building.md](../specifications/consensus-building.md)
- BDD Feature: [tests/behavior/features/consensus_building.feature](../tests/behavior/features/consensus_building.feature)
- Issue: [issues/consensus-building.md](../issues/consensus-building.md)
- Unit Test: [tests/unit/devsynth/test_consensus.py](../tests/unit/devsynth/test_consensus.py)

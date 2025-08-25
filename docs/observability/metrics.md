# Metrics (Optional, Lightweight)

Status: Minimal, optional metrics are available when the `api` extra is installed (provides `prometheus-client`). When unavailable, metrics helpers degrade to no-ops.

## Overview
DevSynth exposes a tiny observability surface focused on stability:
- No hard dependency on Prometheus. If `prometheus-client` is not importable, metrics calls do nothing.
- Simple helper API in `devsynth.observability.metrics`.
- Low overhead: lazy registration, label keys sorted for stable cardinality.

## Install
- Recommended via Poetry extras:
  poetry install --with dev --extras api

This ensures `prometheus-client` is available.

## API
- increment_counter(name: str, labels: Optional[Dict[str, str]] = None, *, description: str = "") -> None

Example:
```python
from devsynth.observability.metrics import increment_counter

# Example variables from a CLI or service context
_target = "unit-tests"
_smoke = False

increment_counter(
    "devsynth_cli_run_tests_invocations",
    {"target": _target, "smoke": str(_smoke).lower()},
    description="Count of devsynth run-tests CLI invocations",
)
```

## Exposure
When running inside a service that exposes Prometheus metrics (e.g., when adding a FastAPI app under the `api` extra), import the helper and instrument critical paths. The helpers do not start an HTTP server by themselves; exposing `/metrics` remains the responsibility of the hosting application.

## Notes
- Metrics must never interfere with primary behavior. All helpers swallow errors by design.
- Prefer bounded-cardinality labels (target, speed, mode, outcome) over unbounded ones.

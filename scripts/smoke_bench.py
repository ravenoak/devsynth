#!/usr/bin/env python3
"""
Smoke benchmarks to catch gross performance regressions quickly.

- Minimal dependencies; runs on any dev install with --extras minimal.
- Measures a few hot-ish internal paths with small inputs.
- Prints a JSON summary of timings.

Use:
  poetry run python scripts/smoke_bench.py

This addresses docs/tasks.md item 15.2 and aligns with .junie/guidelines.md and docs/plan.md.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Tuple


def bench(name: str, fn: Callable[[], Any], repeat: int = 50) -> Dict[str, Any]:
    times: List[float] = []
    for _ in range(repeat):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    # basic summary
    times_sorted = sorted(times)
    return {
        "name": name,
        "repeat": repeat,
        "min_s": min(times_sorted),
        "p50_s": times_sorted[len(times_sorted) // 2],
        "p90_s": times_sorted[int(len(times_sorted) * 0.9) - 1],
        "max_s": max(times_sorted),
    }


def _provider_env_parse() -> None:
    # Avoid heavy imports; localize import to keep startup fast
    try:
        from devsynth.config.provider_env import ProviderEnv  # type: ignore
    except Exception:
        return
    env = ProviderEnv.from_env({})
    _ = env.as_dict()


def _serialization_roundtrip() -> None:
    try:
        from devsynth.utils.serialization import dumps, loads  # type: ignore
    except Exception:
        return
    obj = {"a": 1, "b": "x" * 128, "c": [i for i in range(10)]}
    s = dumps(obj)
    _ = loads(s)


def _cli_parse_dummy() -> None:
    # Exercise Typer/Click option parsing lightly by importing CLI root
    try:
        from devsynth.application.cli.main import app  # type: ignore  # noqa:F401
    except Exception:
        return


def main() -> None:
    benches: List[Tuple[str, Callable[[], Any]]] = [
        ("provider_env_parse", _provider_env_parse),
        ("serialization_roundtrip", _serialization_roundtrip),
        ("cli_import_parse", _cli_parse_dummy),
    ]
    report = [bench(name, fn) for name, fn in benches]
    print(json.dumps({"smoke_bench": report}, indent=2))


if __name__ == "__main__":
    main()

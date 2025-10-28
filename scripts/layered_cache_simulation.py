#!/usr/bin/env python
"""Simulate layered cache hit rates under different layer counts and access patterns.

The simulation seeds its random number generator to ensure reproducibility.
Re-running the script with identical parameters will produce the same results.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


def generate_access_sequence(
    pattern: str, num_items: int, num_accesses: int, seed: int
) -> list[int]:
    """Generate an access sequence.

    Args:
        pattern: Name of the access pattern (``uniform`` or ``zipf``).
        num_items: Total distinct items.
        num_accesses: Length of the generated sequence.
        seed: Random seed for reproducibility.

    Returns:
        Sequence of item identifiers to access.
    """
    rng = random.Random(seed)
    if pattern == "uniform":
        return [rng.randrange(num_items) for _ in range(num_accesses)]
    if pattern == "zipf":
        weights = [1 / (i + 1) for i in range(num_items)]
        total = sum(weights)
        weights = [w / total for w in weights]
        return rng.choices(range(num_items), weights=weights, k=num_accesses)
    raise ValueError(f"Unknown pattern: {pattern}")


def simulate(
    num_layers: int, access_sequence: list[int]
) -> dict[str, float | int | list[float | int]]:
    """Run a layered cache simulation for a single layer count."""
    caches: list[dict[int, bool]] = [dict() for _ in range(num_layers)]
    hits = [0] * num_layers
    total = 0

    for item in access_sequence:
        total += 1
        found = None
        for layer_idx in range(num_layers):
            if item in caches[layer_idx]:
                hits[layer_idx] += 1
                found = layer_idx
                break
        if found is None:
            caches[-1][item] = True
            found = num_layers - 1
        for promote_idx in range(found):
            caches[promote_idx][item] = True

    per_layer_rate = [h / total for h in hits]
    overall_rate = sum(hits) / total
    return {
        "num_layers": num_layers,
        "total_accesses": total,
        "hits": hits,
        "per_layer_rate": per_layer_rate,
        "overall_rate": overall_rate,
    }


def run_simulation(
    max_layers: int,
    num_items: int,
    num_accesses: int,
    pattern: str,
    output: Path | None,
    chart: Path | None,
) -> list[dict[str, float | int | list[float | int]]]:
    """Run simulations for layer counts from 1 to ``max_layers``."""
    sequence = generate_access_sequence(pattern, num_items, num_accesses, seed=42)
    results = [simulate(layers, sequence) for layers in range(1, max_layers + 1)]

    if output:
        output.write_text(json.dumps(results, indent=2))

    if chart:
        try:
            import matplotlib.pyplot as plt

            layers = [r["num_layers"] for r in results]
            rates = [r["overall_rate"] for r in results]
            plt.figure()
            plt.plot(layers, rates, marker="o")
            plt.title(f"Hit Rate vs Layer Count ({pattern})")
            plt.xlabel("Layer count")
            plt.ylabel("Overall hit rate")
            plt.grid(True)
            fmt = chart.suffix.lstrip(".")
            plt.savefig(chart, format=fmt, bbox_inches="tight")
            plt.close()
        except Exception as exc:  # pragma: no cover - visualization best effort
            print(f"Failed to generate chart: {exc}")

    return results


@dataclass
class SyncStore:
    """Store with pending writes used for synchronization demo."""

    data: dict[int, int]
    pending: dict[int, int]


def synchronize(primary: SyncStore, secondary: SyncStore) -> None:
    """Apply pending updates from ``primary`` to ``secondary``."""

    secondary.data.update(primary.pending)
    primary.pending.clear()


def run_synchronization_simulation(iterations: int = 50) -> None:
    """Demonstrate eventual consistency across two stores."""

    rng = random.Random(42)
    a, b = SyncStore({}, {}), SyncStore({}, {})
    for _ in range(iterations):
        key = rng.randrange(100)
        value = rng.randrange(1000)
        a.data[key] = value
        a.pending[key] = value
        if rng.random() < 0.3:
            synchronize(a, b)
            assert a.data == b.data
    synchronize(a, b)
    assert a.data == b.data
    print(f"Synchronization simulation passed for {iterations} iterations")


def main() -> None:
    """Entrypoint for command-line execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--max-layers", type=int, default=5, help="Max layers to simulate."
    )
    parser.add_argument(
        "--num-items", type=int, default=100, help="Distinct items in dataset."
    )
    parser.add_argument(
        "--num-accesses", type=int, default=5000, help="Number of accesses to simulate."
    )
    parser.add_argument(
        "--pattern",
        choices=["uniform", "zipf"],
        default="uniform",
        help="Access pattern to apply.",
    )
    parser.add_argument(
        "--output", type=Path, help="Optional path to write JSON results."
    )
    parser.add_argument(
        "--chart", type=Path, help="Optional path to write chart image."
    )

    args = parser.parse_args()

    results = run_simulation(
        max_layers=args.max_layers,
        num_items=args.num_items,
        num_accesses=args.num_accesses,
        pattern=args.pattern,
        output=args.output,
        chart=args.chart,
    )
    print(json.dumps(results, indent=2))
    run_synchronization_simulation()


if __name__ == "__main__":
    main()

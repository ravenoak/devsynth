#!/usr/bin/env python3
"""Simulate WSDE/EDRR consensus to validate convergence claims."""
from __future__ import annotations

import random
import sys
from statistics import mean
from typing import List


def run_simulation(
    num_agents: int = 5,
    iterations: int = 100,
    eta: float = 0.2,
    seed: int | None = None,
) -> list[list[float]]:
    """Run a simple WSDE/EDRR consensus simulation.

    Args:
        num_agents: Number of participating agents.
        iterations: Maximum number of EDRR cycles.
        eta: Refinement step size ``0 < eta < 1``.
        seed: Optional random seed for deterministic runs.

    Returns:
        History of agent opinions for each iteration.
    """
    if seed is not None:
        random.seed(seed)
    state = [random.uniform(-1, 1) for _ in range(num_agents)]
    history = [state.copy()]
    for _ in range(iterations):
        expand = [s + random.gauss(0, 0.1) for s in state]
        avg = mean(expand)
        state = [s - eta * (s - avg) for s in expand]
        history.append(state.copy())
        if max(abs(s - avg) for s in state) < 1e-3:
            break
    return history


def _recursive_depth(depth: int, max_depth: int) -> int:
    """Simple recursive function to illustrate depth limits."""
    if depth >= max_depth:
        return depth
    return _recursive_depth(depth + 1, max_depth)


def demonstrate_recursion_depth() -> None:
    """Show how recursion depth limits enforce termination."""
    safe_depth = _recursive_depth(0, 10)
    print(f"Safe recursion depth reached: {safe_depth}")
    try:
        _recursive_depth(0, sys.getrecursionlimit() + 1)
    except RecursionError:
        print("RecursionError: maximum depth exceeded")


def main() -> None:
    """Run the simulation and print summary statistics."""
    history = run_simulation()
    final = history[-1]
    print(f"Final opinions: {final}")
    deviation = max(final) - min(final)
    print(f"Deviation: {deviation:.4f}")
    print(f"Iterations: {len(history) - 1}")
    demonstrate_recursion_depth()


if __name__ == "__main__":
    main()

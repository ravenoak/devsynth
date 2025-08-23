#!/usr/bin/env python3
"""Simulate WSDE/EDRR consensus to validate convergence claims."""
from __future__ import annotations

import random
from statistics import mean
from typing import List


def run_simulation(
    num_agents: int = 5, iterations: int = 100, eta: float = 0.2
) -> List[List[float]]:
    """Run a simple WSDE/EDRR consensus simulation.

    Args:
        num_agents: Number of participating agents.
        iterations: Maximum number of EDRR cycles.
        eta: Refinement step size ``0 < eta < 1``.

    Returns:
        History of agent opinions for each iteration.
    """
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


def main() -> None:
    """Run the simulation and print summary statistics."""
    history = run_simulation()
    final = history[-1]
    print(f"Final opinions: {final}")
    deviation = max(final) - min(final)
    print(f"Deviation: {deviation:.4f}")
    print(f"Iterations: {len(history) - 1}")


if __name__ == "__main__":
    main()

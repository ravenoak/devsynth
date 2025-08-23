import pytest

from scripts.wsde_edrr_simulation import run_simulation


@pytest.mark.fast
def test_simulation_converges() -> None:
    """Simulation should drive agent opinions toward consensus. ReqID: SIM-1"""
    history = run_simulation(num_agents=3, iterations=200, eta=0.2, seed=2)
    final = history[-1]
    assert max(final) - min(final) < 0.1

import os

import pytest


@pytest.mark.fast
def test_deterministic_seed_fixture_sets_env_vars():
    """The deterministic_seed fixture should set DEVSYNTH_TEST_SEED and PYTHONHASHSEED.

    ReqID: TEST-INFRA-SEED-1
    """
    # The fixture is autouse at session scope; simply assert environment is prepared.
    seed = os.environ.get("DEVSYNTH_TEST_SEED")
    pyhash = os.environ.get("PYTHONHASHSEED")

    assert (
        seed is not None and seed.isdigit()
    ), "DEVSYNTH_TEST_SEED should be set to a numeric value by the deterministic_seed fixture"
    assert (
        pyhash is not None and pyhash.isdigit()
    ), "PYTHONHASHSEED should be set to a numeric value for subprocess determinism"

    # Sanity: typically equal to the seed value unless overridden before pytest start
    # We do not strictly require equality because PYTHONHASHSEED can be pre-set by the runner.
    if seed and pyhash:
        assert seed.isdigit() and pyhash.isdigit()

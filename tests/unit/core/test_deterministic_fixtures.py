import os
import random

import pytest


@pytest.mark.fast
def test_deterministic_seed_sets_env_and_random_sequence():
    assert os.environ.get("DEVSYNTH_TEST_SEED") is not None
    assert os.environ.get("PYTHONHASHSEED") == os.environ.get("DEVSYNTH_TEST_SEED")

    seed = int(os.environ["DEVSYNTH_TEST_SEED"])  # provided by fixture
    random.seed(seed)
    seq1 = [random.randint(0, 1000000) for _ in range(5)]
    random.seed(seed)
    seq2 = [random.randint(0, 1000000) for _ in range(5)]
    assert seq1 == seq2


@pytest.mark.fast
def test_mock_datetime_fixture_freezes_time(mock_datetime):
    import time as _time
    from datetime import datetime as _dt

    fixed_dt = _dt(2025, 1, 1, 12, 0, 0)
    assert _dt.now() == fixed_dt
    assert _dt.utcnow() == fixed_dt
    assert int(_time.time()) == int(fixed_dt.timestamp())


@pytest.mark.fast
def test_mock_uuid_fixture_returns_fixed_uuid(mock_uuid):
    import uuid as _uuid

    val1 = _uuid.uuid4()
    val2 = _uuid.uuid4()
    assert str(val1) == "12345678-1234-5678-1234-567812345678"
    assert val1 == val2

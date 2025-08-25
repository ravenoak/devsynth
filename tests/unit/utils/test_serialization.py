import json
from pathlib import Path

import pytest

from devsynth.utils.serialization import dumps_deterministic, loads, dump_to_file, load_from_file
from devsynth.config.provider_env import ProviderEnv


@pytest.mark.fast
def test_dumps_deterministic_round_trip_simple():
    obj = {"b": 2, "a": 1, "nested": {"z": [3, 2, 1], "ä": "ü"}}
    s = dumps_deterministic(obj)
    # deterministic: trailing newline present
    assert s.endswith("\n")
    # deterministic: keys sorted (a before b, nested before others)
    # rather than asserting exact string, ensure that removing newline parses identically
    parsed = loads(s)
    assert parsed == obj


@pytest.mark.fast
def test_dump_and_load_file_round_trip(tmp_path: Path):
    obj = {"x": 1, "y": [1, 2, 3]}
    p = tmp_path / "data.json"
    dump_to_file(str(p), obj)
    assert p.exists()
    content = p.read_text(encoding="utf-8")
    # Ensure single trailing newline
    assert content.endswith("\n")
    assert not content.endswith("\n\n")
    loaded = load_from_file(str(p))
    assert loaded == obj


@pytest.mark.fast
def test_provider_env_as_dict_deterministic_serialization():
    env = ProviderEnv(provider="stub", offline=True, lmstudio_available=False)
    data = env.as_dict()
    s1 = dumps_deterministic(data)
    s2 = dumps_deterministic({k: data[k] for k in sorted(data.keys(), reverse=True)})
    # Sorted JSON should be identical regardless of input dict key order
    assert s1 == s2
    # Also confirm that loading restores the same mapping
    assert loads(s1) == data

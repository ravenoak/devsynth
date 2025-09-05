import json
import os

import pytest

from devsynth.utils.serialization import (
    dump_to_file,
    dumps_deterministic,
    load_from_file,
    loads,
)


@pytest.mark.fast
def test_dumps_and_loads_deterministic_round_trip_unicode_and_newline():
    obj = {"b": 2, "a": "☃"}
    s = dumps_deterministic(obj)
    # Deterministic properties
    assert s.endswith("\n"), "Output must end with a single newline"
    # Sorted keys yields a comes before b
    assert s.startswith('{"a":'), f"Unexpected start: {s!r}"
    # Loads should tolerate the trailing newline
    parsed = loads(s)
    assert parsed == {"a": "☃", "b": 2}


@pytest.mark.fast
def test_dump_and_load_file_round_trip_handles_utf8(tmp_path):
    path = tmp_path / "data.json"
    payload = {"greeting": "こんにちは", "n": 3}
    dump_to_file(str(path), payload)
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.endswith("\n"), "File content should end with newline"
    # Load and compare
    loaded = load_from_file(str(path))
    assert loaded == payload


@pytest.mark.fast
def test_loads_accepts_without_trailing_newline():
    obj = {"k": 1}
    s = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # No newline on purpose
    assert loads(s) == obj

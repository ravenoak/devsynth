from pathlib import Path

import pytest

from devsynth.utils.serialization import (
    dump_to_file,
    dumps_deterministic,
    load_from_file,
    loads,
)


@pytest.mark.fast
def test_loads_tolerates_missing_and_single_trailing_newline():
    """ReqID: UT-SER-01 — loads tolerates missing or duplicate trailing newline."""
    obj = {"a": 1, "b": [3, 2, 1]}
    s = dumps_deterministic(obj)
    assert s.endswith("\n")
    # Remove trailing newline and ensure parser still accepts it
    s_no_nl = s[:-1]
    assert loads(s_no_nl) == obj
    # Double newline should still parse; json parser tolerates trailing whitespace
    s_double = s + "\n"
    assert loads(s_double) == obj


@pytest.mark.fast
def test_dump_to_file_overwrites_and_keeps_single_newline(tmp_path: Path):
    """ReqID: UT-SER-02 — dump_to_file overwrites and keeps single newline invariant."""
    p = tmp_path / "data.json"
    dump_to_file(str(p), {"x": 1})
    first = p.read_text(encoding="utf-8")
    assert first.endswith("\n") and not first.endswith("\n\n")
    # Overwrite with different content keeps invariant
    dump_to_file(str(p), {"y": 2})
    second = p.read_text(encoding="utf-8")
    assert second.endswith("\n") and not second.endswith("\n\n")
    assert load_from_file(str(p)) == {"y": 2}

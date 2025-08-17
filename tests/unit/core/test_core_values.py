import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "devsynth.core.values",
    Path(__file__).resolve().parents[3] / "src" / "devsynth" / "core" / "values.py",
)
values_mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
import sys

sys.modules[spec.name] = values_mod
spec.loader.exec_module(values_mod)
CoreValues = values_mod.CoreValues
find_value_conflicts = values_mod.find_value_conflicts
check_report_for_value_conflicts = values_mod.check_report_for_value_conflicts


pytestmark = pytest.mark.medium


def test_load_core_values_succeeds(tmp_path):
    """Test loading core values from YAML."""
    values_dir = tmp_path / ".devsynth"
    values_dir.mkdir()
    (values_dir / "values.yml").write_text("- integrity\n- transparency\n")
    values = CoreValues.load(tmp_path)
    assert values.statements == ["integrity", "transparency"]


def test_find_value_conflicts_succeeds():
    """Test conflict detection within text."""
    values = CoreValues(["integrity", "transparency"])
    text = "This plan would violate integrity while remaining transparent."
    assert find_value_conflicts(text, values) == ["integrity"]


def test_check_report_for_value_conflicts_succeeds(tmp_path):
    """Test conflict detection within a report structure."""
    values_dir = tmp_path / ".devsynth"
    values_dir.mkdir()
    (values_dir / "values.yml").write_text("- honesty\n")
    values = CoreValues.load(tmp_path)
    report = {"notes": "This approach may violate honesty in execution."}
    conflicts = check_report_for_value_conflicts(report, values)
    assert conflicts == ["honesty"]

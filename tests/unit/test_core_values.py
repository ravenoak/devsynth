from devsynth.core import CoreValues, check_report_for_value_conflicts


def test_load_core_values(tmp_path):
    values_dir = tmp_path / ".devsynth"
    values_dir.mkdir()
    (values_dir / "values.yml").write_text("- integrity\n- transparency\n")

    values = CoreValues.load(tmp_path)
    assert values.statements == ["integrity", "transparency"]


def test_conflict_detection(tmp_path):
    values_dir = tmp_path / ".devsynth"
    values_dir.mkdir()
    (values_dir / "values.yml").write_text("- honesty\n")

    values = CoreValues.load(tmp_path)
    report = {"notes": "This approach may violate honesty in execution."}
    conflicts = check_report_for_value_conflicts(report, values)
    assert conflicts == ["honesty"]

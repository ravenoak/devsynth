import pytest

from scripts import enhanced_test_parser as etp


def test_build_test_path_integration_component():
    path = etp.build_test_path("integration", "api_workflow", component="interface")
    assert path == "tests/integration/interface/test_api_workflow.py"


def test_build_test_path_integration_missing_component():
    with pytest.raises(ValueError) as exc:
        etp.build_test_path("integration", "api_workflow")
    assert "component" in str(exc.value)


def test_build_test_path_unit():
    assert etp.build_test_path("unit", "calc") == "tests/unit/test_calc.py"

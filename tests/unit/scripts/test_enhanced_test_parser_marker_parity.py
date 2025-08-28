# We import the scripts as modules for direct function access
import importlib.util
import sys
import textwrap
from pathlib import Path

import pytest


def _import_module_from_path(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


@pytest.mark.fast
def test_parametrize_speed_marker_parity(tmp_path: Path):
    # Create a synthetic test file that uses only pytest.param speed markers
    test_code = textwrap.dedent(
        """
        import pytest

        @pytest.mark.parametrize(
            "x",
            [
                pytest.param(1, marks=pytest.mark.medium),
                pytest.param(2, marks=pytest.mark.medium),
            ],
        )
        def test_derived_speed_from_params(x):
            assert x in (1, 2)
        """
    )
    file_path = tmp_path / "test_sample_param_speed.py"
    file_path.write_text(test_code)

    # Load enhanced_test_parser from scripts
    etp = _import_module_from_path(
        "enhanced_test_parser",
        Path(__file__).parents[3] / "scripts" / "enhanced_test_parser.py",
    )
    vtm = _import_module_from_path(
        "verify_test_markers",
        Path(__file__).parents[3] / "scripts" / "verify_test_markers.py",
    )

    # Parse using enhanced test parser
    parsed = etp.parse_test_file(str(file_path))
    # Find our test
    target = [
        t for t in parsed["tests"] if t["name"] == "test_derived_speed_from_params"
    ]
    assert target, "Expected test to be discovered"
    test_entry = target[0]
    assert test_entry["markers"] == [
        "medium"
    ], "Enhanced parser should derive 'medium' from pytest.param marks"

    # Verify marker discipline with verify_test_markers (should be no violations)
    text = file_path.read_text()
    violations = vtm._find_speed_marker_violations(file_path, text)
    assert violations == [], f"Expected no violations, got: {violations}"

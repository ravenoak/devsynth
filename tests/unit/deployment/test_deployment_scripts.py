import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.fast
def test_bootstrap_script_exists():
    """Bootstrap script should be present and executable."""
    script = ROOT / "deployment/bootstrap_env.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)


@pytest.mark.fast
def test_health_check_script_exists():
    """Health check script should be present and executable."""
    script = ROOT / "deployment/health_check.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)

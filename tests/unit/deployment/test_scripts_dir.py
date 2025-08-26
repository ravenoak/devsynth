import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]

@pytest.mark.fast

def test_scripts_bootstrap_exists():
    """Bootstrap script in scripts/deployment should exist and be executable."""
    script = ROOT / "scripts/deployment/bootstrap.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)


@pytest.mark.fast
def test_scripts_health_check_exists():
    """Health check script in scripts/deployment should exist and be executable."""
    script = ROOT / "scripts/deployment/health_check.sh"
    assert script.is_file()
    assert os.access(script, os.X_OK)

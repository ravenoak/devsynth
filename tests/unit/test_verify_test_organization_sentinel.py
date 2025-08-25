import pytest

# Import the organizational checker script as a module
from tests import verify_test_organization as org_checker


@pytest.mark.fast
def test_verify_test_organization_returns_zero():
    """Sentinel: ensure basic test organization check passes quickly.

    This test calls the lightweight organization checker and asserts it
    returns 0 (success). It serves as a guard for marker/test-organization
    constraints without adding runtime overhead.
    """
    assert org_checker.main() == 0

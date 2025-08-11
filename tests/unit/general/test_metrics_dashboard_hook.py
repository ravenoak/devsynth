import pytest

from devsynth.metrics import (
    clear_dashboard_hook,
    get_dashboard_metrics,
    inc_dashboard,
    register_dashboard_hook,
    reset_metrics,
)


@pytest.mark.medium
def test_dashboard_hook_receives_events():
    """Registering a dashboard hook forwards events."""
    reset_metrics()
    received = []

    def hook(event: str) -> None:
        received.append(event)

    register_dashboard_hook(hook)
    inc_dashboard("startup")
    clear_dashboard_hook()

    assert received == ["startup"]
    assert get_dashboard_metrics()["startup"] == 1

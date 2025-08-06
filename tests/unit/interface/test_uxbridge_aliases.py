from devsynth.interface.ux_bridge import UXBridge
import pytest


class DummyBridge(UXBridge):

    def __init__(self) -> None:
        self.calls = []

    def ask_question(self, message, *, choices=None, default=None, show_default=True):
        self.calls.append(("ask_question", message, choices, default, show_default))
        return "ans"

    def confirm_choice(self, message, *, default=False):
        self.calls.append(("confirm_choice", message, default))
        return default

    def display_result(self, message, *, highlight=False):
        self.calls.append(("display_result", message, highlight))


@pytest.mark.slow
@pytest.fixture
def clean_state():
    yield


def test_function(clean_state):
    bridge = DummyBridge()
    result = bridge.prompt("q", choices=["x"], default="x", show_default=False)
    assert result == "ans"
    assert bridge.calls[0] == ("ask_question", "q", ["x"], "x", False)


@pytest.mark.medium
def test_print_alias_delegates():
    bridge = DummyBridge()
    bridge.print("msg", highlight=True)
    assert bridge.calls[0] == ("display_result", "msg", True)

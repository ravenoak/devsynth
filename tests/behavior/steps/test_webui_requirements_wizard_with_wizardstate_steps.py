"""BDD steps exercising the requirements wizard with ``WizardState`` integration."""

from __future__ import annotations

import json
import sys
from types import ModuleType
from typing import Tuple
from unittest.mock import MagicMock, mock_open

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from tests.behavior.feature_paths import feature_path

pytestmark = pytest.mark.fast


scenarios(
    feature_path(
        __file__,
        "..",
        "requirements_wizard",
        "features",
        "general",
        "webui_requirements_wizard_with_wizardstate.feature",
    )
)


@pytest.fixture
def wizard_context(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    """Provide a fully stubbed Streamlit environment for the wizard tests."""

    st = ModuleType("streamlit")

    class SessionState(dict):
        def __getattr__(self, name: str):  # pragma: no cover - defensive
            try:
                return self[name]
            except KeyError as exc:  # pragma: no cover - mimics Streamlit behaviour
                raise AttributeError(name) from exc

        def __setattr__(self, name: str, value):
            self[name] = value

    st.session_state = SessionState()

    context: dict[str, object] = {
        "widget_values": {},
        "next_buttons": (False, False, False),
        "saved_requirements": None,
    }

    st.header = MagicMock()
    st.write = MagicMock()
    st.progress = MagicMock()
    st.markdown = MagicMock()
    st.error = MagicMock()
    st.warning = MagicMock()
    st.success = MagicMock()
    st.info = MagicMock()

    def _value_for_key(key: str | None, default):
        if key is None:
            return default
        return context["widget_values"].get(key, default)

    st.text_input = MagicMock(
        side_effect=lambda label, value="", key=None: _value_for_key(key, value)
    )
    st.text_area = MagicMock(
        side_effect=lambda label, value="", key=None: _value_for_key(key, value)
    )

    def _selectbox(label, options, index=0, key=None):  # noqa: ANN001
        choice = _value_for_key(key, options[index])
        return choice if choice in options else options[index]

    st.selectbox = MagicMock(side_effect=_selectbox)

    def _columns(count: int):
        config: tuple[bool, ...] = context.get("next_buttons", (False,) * count)  # type: ignore[arg-type]
        padded = list(config) + [False] * max(0, count - len(config))
        columns = []
        for idx in range(count):
            column = MagicMock()
            column.button = MagicMock(return_value=padded[idx])
            columns.append(column)
        context["next_buttons"] = (False,) * count
        return columns

    st.columns = MagicMock(side_effect=_columns)

    monkeypatch.setitem(sys.modules, "streamlit", st)

    for env_var in (
        "DEVSYNTH_REQ_TITLE",
        "DEVSYNTH_REQ_DESCRIPTION",
        "DEVSYNTH_REQ_TYPE",
        "DEVSYNTH_REQ_PRIORITY",
        "DEVSYNTH_REQ_CONSTRAINTS",
    ):
        monkeypatch.delenv(env_var, raising=False)

    import importlib

    import devsynth.interface.webui as webui

    importlib.reload(webui)

    ui = webui.WebUI()
    ui.display_result = MagicMock()

    from devsynth.domain.models.requirement import RequirementPriority, RequirementType

    initial_state = {
        "title": "",
        "description": "",
        "type": RequirementType.FUNCTIONAL.value,
        "priority": RequirementPriority.MEDIUM.value,
        "constraints": "",
        "wizard_started": True,
    }

    def get_state():
        from devsynth.interface.webui_state import WizardState

        return WizardState("requirements_wizard", 5, initial_state)

    context.update(
        ui=ui,
        st=st,
        get_state=get_state,
        initial_state=initial_state,
    )

    return context


def _run_wizard(context: dict[str, object]) -> None:
    context["ui"]._requirements_wizard()  # type: ignore[index]


def _schedule_buttons(
    context: dict[str, object],
    *,
    prev: bool = False,
    nxt: bool = False,
    cancel: bool = False,
) -> None:
    context["next_buttons"] = (prev, nxt, cancel)


@given("the requirements wizard is ready")
def wizard_is_ready(wizard_context: dict[str, object]) -> None:
    _run_wizard(wizard_context)


@when(parsers.parse('I enter "{title}" for the requirement title'))
def enter_title(wizard_context: dict[str, object], title: str) -> None:
    wizard_context["widget_values"]["requirements_title_input"] = title  # type: ignore[index]
    _run_wizard(wizard_context)


@when("I advance to the next requirements step")
def advance_step(wizard_context: dict[str, object]) -> None:
    _schedule_buttons(wizard_context, nxt=True)
    _run_wizard(wizard_context)
    _run_wizard(wizard_context)


@when(parsers.parse('I enter "{description}" for the requirement description'))
def enter_description(wizard_context: dict[str, object], description: str) -> None:
    wizard_context["widget_values"]["requirements_description_input"] = description  # type: ignore[index]
    _run_wizard(wizard_context)


@when("I go back to the previous requirements step")
def go_back(wizard_context: dict[str, object]) -> None:
    _schedule_buttons(wizard_context, prev=True)
    _run_wizard(wizard_context)
    _run_wizard(wizard_context)


@then(parsers.parse('the wizard stores the title "{title}"'))
def assert_title_persisted(wizard_context: dict[str, object], title: str) -> None:
    state = wizard_context["get_state"]()  # type: ignore[operator]
    assert state.get("title") == title


@then(parsers.parse('the wizard keeps the description "{description}" for step 2'))
def assert_description_persisted(
    wizard_context: dict[str, object], description: str
) -> None:
    state = wizard_context["get_state"]()  # type: ignore[operator]
    assert state.get("description") == description


@when(parsers.parse('I choose "{req_type}" as the requirement type'))
def choose_requirement_type(wizard_context: dict[str, object], req_type: str) -> None:
    wizard_context["widget_values"]["requirements_type_select"] = req_type  # type: ignore[index]
    _run_wizard(wizard_context)


@when(parsers.parse('I choose "{priority}" as the requirement priority'))
def choose_requirement_priority(
    wizard_context: dict[str, object], priority: str
) -> None:
    wizard_context["widget_values"]["requirements_priority_select"] = priority  # type: ignore[index]
    _run_wizard(wizard_context)


@when(parsers.parse('I enter "{constraints}" for the requirement constraints'))
def enter_constraints(wizard_context: dict[str, object], constraints: str) -> None:
    wizard_context["widget_values"]["requirements_constraints_input"] = constraints  # type: ignore[index]
    _run_wizard(wizard_context)


@when("I finish the requirements wizard")
def finish_wizard(
    wizard_context: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    saved: dict[str, object] = {}

    import builtins

    file_mock = mock_open()
    real_open = builtins.open

    def selective_open(path, *args, **kwargs):  # noqa: ANN001
        if path == "requirements_wizard.json":
            return file_mock(path, *args, **kwargs)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr("builtins.open", selective_open)

    _schedule_buttons(wizard_context, nxt=True)
    _run_wizard(wizard_context)

    handle = file_mock()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    if written:
        saved = json.loads(written)

    wizard_context["saved_requirements"] = saved


@then("the requirements wizard returns to step 1")
def assert_wizard_reset(wizard_context: dict[str, object]) -> None:
    state = wizard_context["get_state"]()  # type: ignore[operator]
    assert state.get_current_step() == 1


@then("the wizard clears the captured requirement data")
def assert_state_cleared(wizard_context: dict[str, object]) -> None:
    state = wizard_context["get_state"]()  # type: ignore[operator]
    assert state.get("title") == ""
    assert state.get("description") == ""
    assert state.get("constraints") == ""


@then("the requirements summary is saved")
def assert_summary_saved(wizard_context: dict[str, object]) -> None:
    saved = wizard_context.get("saved_requirements")
    assert isinstance(saved, dict) and saved
    assert saved["title"] == "User Login"
    assert saved["priority"].lower() == "high"

import types
from typing import Any, Dict, List, Optional

import pytest

from devsynth.application.cli.commands.config_cmd import (
    config_cmd,
    enable_feature_cmd,
)


class DummyConfig:
    def __init__(self, initial: dict[str, Any] | None = None) -> None:
        data = dict(initial or {})
        # expose attributes for getattr/setattr
        for k, v in data.items():
            setattr(self, k, v)
        # features often present in config; start empty unless provided
        self.features = data.get("features", {})

    def as_dict(self) -> dict[str, Any]:
        # Collect public attributes into a dict for save_config serialization
        d: dict[str, Any] = {
            k: v for k, v in self.__dict__.items() if not k.startswith("_")
        }
        return d


class CapturingBridge:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def display_result(self, msg: str, highlight: bool = True) -> None:  # noqa: D401
        self.messages.append(msg)


@pytest.mark.fast
def test_config_cmd_displays_all_config(monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange stubs/mocks
    dummy_config = DummyConfig({"alpha": "1", "beta": "2"})

    class DummyLoader:
        @staticmethod
        def load():
            return types.SimpleNamespace(config=dummy_config)

    def fake_execute_command(name: str, args: dict[str, Any]) -> dict[str, Any]:
        assert name == "config"
        # simulate returning the full config map
        return {"success": True, "config": dummy_config.as_dict()}

    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.UnifiedConfigLoader",
        DummyLoader,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.workflows.execute_command",
        fake_execute_command,
    )

    bridge = CapturingBridge()

    # Act
    config_cmd(bridge=bridge)

    # Assert
    joined = "\n".join(bridge.messages)
    assert "DevSynth Configuration:" in joined
    assert "alpha:" in joined and "beta:" in joined


@pytest.mark.fast
def test_config_cmd_update_key_value_saves_and_reports(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_config = DummyConfig({"model": "old"})

    class DummyLoader:
        @staticmethod
        def load():
            return types.SimpleNamespace(config=dummy_config)

    def fake_execute_command(name: str, args: dict[str, Any]) -> dict[str, Any]:
        assert args.get("key") == "model" and args.get("value") == "gpt-4"
        return {"success": True}

    save_called = {}

    def fake_save_config(model_obj, use_pyproject: bool = False) -> None:  # type: ignore[no-untyped-def]
        # capture that save was triggered with updated config
        save_called["called"] = True
        assert isinstance(model_obj, object)
        assert use_pyproject in (True, False)

    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.UnifiedConfigLoader",
        DummyLoader,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.workflows.execute_command",
        fake_execute_command,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.save_config",
        fake_save_config,
    )

    bridge = CapturingBridge()

    # Act
    config_cmd(key="model", value="gpt-4", bridge=bridge)

    # Assert
    assert save_called.get("called") is True
    assert any("Configuration updated: model = gpt-4" in m for m in bridge.messages)
    # ensure in-memory object was updated before save
    assert getattr(dummy_config, "model") == "gpt-4"


@pytest.mark.fast
def test_config_cmd_list_models_displays_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dummy_config = DummyConfig({})

    class DummyLoader:
        @staticmethod
        def load():
            return types.SimpleNamespace(config=dummy_config)

    def fake_execute_command(name: str, args: dict[str, Any]) -> dict[str, Any]:
        assert args.get("list_models") is True
        return {"success": True, "models": ["m1", "m2"]}

    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.UnifiedConfigLoader",
        DummyLoader,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.workflows.execute_command",
        fake_execute_command,
    )

    bridge = CapturingBridge()
    config_cmd(list_models=True, bridge=bridge)

    joined = "\n".join(bridge.messages)
    assert "Available LLM Models:" in joined
    assert "m1" in joined and "m2" in joined


@pytest.mark.fast
def test_enable_feature_cmd_updates_and_saves(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy_config = DummyConfig({})

    class DummyLoader:
        @staticmethod
        def load():
            return types.SimpleNamespace(config=dummy_config)

    save_called = {"count": 0}
    refreshed = {"count": 0}

    def fake_save_config(model_obj, use_pyproject: bool = False) -> None:  # type: ignore[no-untyped-def]
        save_called["count"] += 1

    def fake_refresh() -> None:
        refreshed["count"] += 1

    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.UnifiedConfigLoader",
        DummyLoader,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.save_config",
        fake_save_config,
    )
    monkeypatch.setattr(
        "devsynth.application.cli.commands.config_cmd.feature_flags.refresh",
        fake_refresh,
    )

    bridge = CapturingBridge()

    # Act
    enable_feature_cmd("code_generation", bridge=bridge)

    # Assert
    # features dict updated
    assert dummy_config.features.get("code_generation") is True
    # save and refresh called
    assert save_called["count"] == 1
    assert refreshed["count"] == 1
    # user-visible message emitted
    assert any("Feature 'code_generation' enabled." in m for m in bridge.messages)

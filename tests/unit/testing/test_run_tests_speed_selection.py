from __future__ import annotations

from typing import Any

import pytest

import devsynth.testing.run_tests as rt

from .run_tests_test_utils import build_batch_metadata


def _noop(*_args: Any, **_kwargs: Any) -> None:
    return None


@pytest.fixture(autouse=True)
def _patch_coverage_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Neutralize coverage side effects during marker regression tests."""

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", _noop)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", _noop)
    monkeypatch.setattr(rt, "ensure_pytest_cov_plugin_env", lambda _env: False)
    monkeypatch.setattr(rt, "ensure_pytest_bdd_plugin_env", lambda _env: False)


@pytest.mark.fast
def test_run_tests_merges_fast_and_medium_collections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Multiple speed categories collect and execute a unified node list."""

    collect_calls: list[str | None] = []

    def fake_collect(target: str, speed: str | None) -> list[str]:
        collect_calls.append(speed)
        if speed == "fast":
            return ["tests/unit/test_fast.py::test_fast_case"]
        if speed == "medium":
            return ["tests/unit/test_medium.py::test_medium_case"]
        return []

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect)

    recorded: dict[str, Any] = {}

    def fake_single_batch(
        config: rt.SingleBatchRequest,
    ) -> rt.BatchExecutionResult:
        recorded["node_ids"] = list(config.node_ids)
        recorded["marker_expr"] = config.marker_expr
        return True, "ok", build_batch_metadata("batch-speed-1")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_single_batch)
    monkeypatch.setenv("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", "true")

    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast", "medium"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=25,
        maxfail=None,
    )

    assert ok is True
    assert output == "ok"
    assert collect_calls == ["fast", "medium"]
    assert recorded["node_ids"] == [
        "tests/unit/test_fast.py::test_fast_case",
        "tests/unit/test_medium.py::test_medium_case",
    ]
    marker_expr = recorded["marker_expr"]
    assert "fast or medium" in marker_expr
    assert "not memory_intensive" in marker_expr


@pytest.mark.fast
def test_run_tests_defaults_to_fast_and_medium_when_unspecified(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Omitting speed categories falls back to fast+medium coverage."""

    collect_calls: list[str | None] = []

    def fake_collect(target: str, speed: str | None) -> list[str]:
        collect_calls.append(speed)
        if speed == "fast":
            return ["tests/unit/test_fast.py::test_a"]
        if speed == "medium":
            return ["tests/unit/test_medium.py::test_b"]
        return []

    monkeypatch.setattr(rt, "collect_tests_with_cache", fake_collect)

    def fake_batch(config: rt.SingleBatchRequest) -> rt.BatchExecutionResult:
        return True, config.marker_expr, build_batch_metadata("batch-speed-2")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_batch)
    monkeypatch.setenv("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", "true")

    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=25,
        maxfail=None,
    )

    assert ok is True
    assert collect_calls == ["fast", "medium"]
    assert "fast or medium" in output


@pytest.mark.fast
def test_run_tests_excludes_gui_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """GUI-marked tests are filtered unless the resource flag opts in."""

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda _target, _speed: ["tests/unit/test_gui.py::test_panel"],
    )

    captured: dict[str, Any] = {}

    def fake_batch(config: rt.SingleBatchRequest) -> rt.BatchExecutionResult:
        captured["marker_expr"] = config.marker_expr
        return True, "", build_batch_metadata("batch-speed-3")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_batch)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", raising=False)

    ok, _ = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=25,
        maxfail=None,
    )

    assert ok is True
    assert "not gui" in captured["marker_expr"]


@pytest.mark.fast
def test_run_tests_allows_gui_when_requested(monkeypatch: pytest.MonkeyPatch) -> None:
    """Explicit GUI markers suppress the automatic GUI exclusion."""

    monkeypatch.setattr(
        rt,
        "collect_tests_with_cache",
        lambda _target, _speed: ["tests/unit/test_gui.py::test_panel"],
    )

    captured: dict[str, Any] = {}

    def fake_batch(config: rt.SingleBatchRequest) -> rt.BatchExecutionResult:
        captured["marker_expr"] = config.marker_expr
        return True, "", build_batch_metadata("batch-speed-4")

    monkeypatch.setattr(rt, "_run_single_test_batch", fake_batch)
    monkeypatch.delenv("DEVSYNTH_RESOURCE_WEBUI_AVAILABLE", raising=False)

    ok, _ = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=25,
        maxfail=None,
        extra_marker="gui",
    )

    assert ok is True
    marker_expr = captured["marker_expr"]
    assert "not gui" not in marker_expr
    assert "gui" in marker_expr

from typing import Any

import pytest

import devsynth.testing.run_tests as rt


class DummyProc:
    def __init__(self, args: list[str]) -> None:
        self.args = args
        self.returncode = 0

    def communicate(self) -> tuple[str, str]:
        return ("ok", "")


@pytest.mark.fast
def test_speed_marker_merged_with_lmstudio_keyword_filter(
    monkeypatch,
) -> None:  # noqa: E501
    """ReqID: RT-03 — LMStudio keyword (-k) plus merged speed marker (-m) handling."""

    # Capture the collect/run invocations
    recorded: dict[str, Any] = {"runs": []}

    def fake_run(
        cmd,  # noqa: ANN001
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
        **_kwargs: Any,
    ):  # type: ignore[no-redef]
        # Record calls to inspect '-k' and '-m' usage
        recorded["runs"].append(list(cmd))

        class R:
            def __init__(self) -> None:
                self.returncode = 0
                # Minimal deterministic node ids
                self.stdout = "tests/unit/test_a.py::t1\n" "tests/unit/test_b.py::t2\n"
                self.stderr = ""

        return R()

    def fake_popen(
        args,  # noqa: ANN001
        stdout=None,  # noqa: ANN001
        stderr=None,  # noqa: ANN001
        text=None,  # noqa: ANN001
        env=None,  # noqa: ANN001
    ):  # type: ignore[no-redef]
        recorded["popen_args"] = list(args)
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, _output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    # Ensure collect command used '-k lmstudio'
    # with merged speed marker expression
    runs = recorded["runs"]
    collect_only = "--collect-only"
    collect_cmds = [c for c in runs if collect_only in c]
    assert collect_cmds, "no collect invocations recorded"
    collect = collect_cmds[-1]
    assert "-k" in collect
    assert "lmstudio" in collect
    # Find the marker expression argument and verify it matches
    # the expected expression: fast and not memory_intensive
    assert "-m" in collect
    m_indices = [i for i, v in enumerate(collect) if v == "-m"]
    m_index = m_indices[-1]
    marker_expr = collect[m_index + 1]
    # The extra marker should NOT be embedded in '-m'
    # when using keyword filtering
    assert marker_expr == "fast and not memory_intensive"


@pytest.mark.fast
def test_global_marker_with_lmstudio_keyword_filter(monkeypatch) -> None:
    """ReqID: RT-04 — LMStudio keyword filter works with global marker.

    Ensures '-m not memory_intensive' is used.
    """

    recorded: dict[str, Any] = {"runs": []}

    def fake_run(
        cmd,  # noqa: ANN001
        check: bool = False,
        capture_output: bool = False,
        text: bool = False,
        **_kwargs: Any,
    ):  # type: ignore[no-redef]
        recorded["runs"].append(list(cmd))

        class R:
            def __init__(self) -> None:
                self.returncode = 0
                self.stdout = "tests/unit/test_x.py::t1\n"
                self.stderr = ""

        return R()

    def fake_popen(
        args,  # noqa: ANN001
        stdout=None,  # noqa: ANN001
        stderr=None,  # noqa: ANN001
        text=None,  # noqa: ANN001
        env=None,  # noqa: ANN001
    ):  # type: ignore[no-redef]
        recorded["popen_args"] = list(args)
        return DummyProc(list(args))

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", fake_popen)

    success, _output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker='requires_resource("lmstudio")',
    )

    assert success is True
    # The collect invocation should include '-k lmstudio'
    # and '-m not memory_intensive'
    runs = recorded["runs"]
    collect_cmds = [c for c in runs if "--collect-only" in c]
    assert collect_cmds, "no collect invocations recorded"
    collect = collect_cmds[-1]
    assert "-k" in collect and "lmstudio" in collect
    assert "-m" in collect
    m_indices = [i for i, v in enumerate(collect) if v == "-m"]
    m_index = m_indices[-1]
    marker_expr = collect[m_index + 1]
    assert "not memory_intensive" in marker_expr
    assert "requires_resource" not in marker_expr

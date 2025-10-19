import re
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.mark.fast
def test_run_tests_report_injects_html_args_and_creates_dir(monkeypatch, tmp_path):
    """
    ReqID: TR-RT-12 — Report HTML generation and directory creation.

    Validate that when report=True, run_tests:
    - adds --html=<test_reports/.../target>/report.html and --self-contained-html
    - creates the report directory path
    - executes pytest with node ids (non-parallel path)
    """

    # Arrange a tmp tests dir and map unit-tests target to it
    tests_dir = tmp_path / "tests" / "unit"
    tests_dir.mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tests_dir))

    # Collection returns a couple of node ids
    collected = [
        "tests/unit/test_alpha.py::test_a",
        "tests/unit/test_beta.py::test_b",
    ]

    def fake_run(
        cmd,
        check=False,
        capture_output=False,
        text=False,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        if "--collect-only" in cmd:
            return SimpleNamespace(stdout="\n".join(collected), stderr="", returncode=0)
        return SimpleNamespace(stdout="", stderr="", returncode=0)

    seen_cmds: list[list[str]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=True, env=None
        ):  # noqa: ANN001
            seen_cmds.append(cmd)
            self.returncode = 0

        def communicate(self):  # noqa: D401
            return ("", "")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    # Act
    ok, output = rt.run_tests(
        target="unit-tests",
        speed_categories=[
            "fast"
        ],  # go through segmented-speed path without segmentation
        verbose=False,
        report=True,
        parallel=False,
        segment=False,
        segment_size=50,
        maxfail=None,
        extra_marker=None,
    )

    # Assert
    assert ok is True
    assert output == ""

    # One run command should be seen
    assert seen_cmds, "expected a pytest invocation"
    cmd = seen_cmds[0]

    # It should include --html=<path>/report.html and --self-contained-html
    html_args = [arg for arg in cmd if arg.startswith("--html=")]
    assert html_args, f"--html arg not found in: {cmd}"
    assert "--self-contained-html" in cmd

    # Validate the HTML path format and that directory exists
    html_arg = html_args[0]
    m = re.match(
        r"^--html=(test_reports/\d{8}_\d{6}/unit-tests)/report.html$", html_arg
    )
    assert m, f"unexpected html path format: {html_arg}"
    report_dir_rel = m.group(1)

    report_dir = Path(report_dir_rel)
    assert report_dir.exists(), f"report directory not created: {report_dir}"

"""Focused coverage tests for ``devsynth.testing.run_tests`` CLI helpers."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

import devsynth.testing.run_tests as rt


@pytest.fixture(autouse=True)
def _isolate_artifact_helpers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent filesystem side effects during helper orchestration tests."""

    monkeypatch.setattr(rt, "_reset_coverage_artifacts", lambda: None)
    monkeypatch.setattr(rt, "_ensure_coverage_artifacts", lambda: None)


def _assert_plugins_in_addopts(addopts: str) -> None:
    """Assert pytest-cov and pytest-bdd plugins are present in addopts."""

    normalized = addopts.strip()
    assert normalized, "PYTEST_ADDOPTS should not be empty when plugins are injected"
    assert (
        "-p pytest_cov" in normalized or "-ppytest_cov" in normalized
    ), f"pytest-cov plugin missing: {normalized}"
    assert (
        "-p pytest_bdd.plugin" in normalized or "-ppytest_bdd.plugin" in normalized
    ), f"pytest-bdd plugin missing: {normalized}"


def _assert_plugins_in_env(env: dict[str, str]) -> None:
    """Assert plugin reinjection occurred for the provided environment mapping."""

    _assert_plugins_in_addopts(env.get("PYTEST_ADDOPTS", ""))


@pytest.mark.fast
def test_segmented_batches_inject_plugins_and_emit_tips(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """ReqID: RUN-TESTS-SEGMENT-CLI-1 — Segmented runs inject plugins and tips."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_a = tmp_path / "test_alpha.py"
    test_b = tmp_path / "test_beta.py"
    test_a.write_text("def test_one():\n    assert True\n")
    test_b.write_text("def test_two():\n    assert True\n")

    collect_payload = "\n".join(
        [
            f"{test_a}::test_one",
            f"{test_b}::test_two",
        ]
    )

    def fake_collect(
        cmd, check=False, capture_output=True, text=True, timeout=None, **kwargs
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(returncode=0, stdout=collect_payload, stderr="")

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)

    batch_plan = iter(
        [
            {
                "returncode": 1,
                "stdout": "",
                "stderr": "FAIL Required test coverage of 90% not reached.",
            },
            {
                "returncode": 1,
                "stdout": "",
                "stderr": "FAIL Required test coverage of 90% not reached.",
            },
        ]
    )

    popen_envs: list[dict[str, str]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=True, env=None
        ):  # noqa: ANN001
            popen_envs.append(dict(env or {}))
            try:
                step = next(batch_plan)
            except StopIteration as exc:  # pragma: no cover - guards test integrity
                raise AssertionError("Unexpected segmented batch invocation") from exc
            self.returncode = step["returncode"]
            self._stdout = step["stdout"]
            self._stderr = step["stderr"]

        def communicate(self):  # noqa: D401 - mimic subprocess API
            """Return the stubbed stdout/stderr pair."""

            # Combine stdout and stderr as the real subprocess does when stderr=STDOUT
            combined_output = self._stdout
            if self._stderr:
                combined_output += self._stderr
            return combined_output, ""

    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)
    caplog.set_level(logging.INFO, logger="devsynth.testing.run_tests")

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker=None,
    )

    assert success is False
    assert output.count("Troubleshooting tips:") == 2
    assert "FAIL Required test coverage" in output

    assert popen_envs, "Expected at least one segmented batch invocation"
    for captured_env in popen_envs:
        _assert_plugins_in_env(captured_env)


@pytest.mark.fast
def test_segmented_batch_exception_emits_tips_and_plugins(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ReqID: RUN-TESTS-SEGMENT-CLI-2 — Exceptions surface tips and preserve plugins."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_file = tmp_path / "test_segment.py"
    test_file.write_text("def test_fail():\n    assert True\n")

    def fake_collect(
        cmd, check=False, capture_output=True, text=True, timeout=None, **kwargs
    ):  # noqa: ANN001
        return SimpleNamespace(
            returncode=0, stdout=f"{test_file}::test_fail\n", stderr=""
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)

    captured_envs: list[dict[str, str]] = []

    def exploding_batch(
        cmd, stdout=None, stderr=None, text=True, env=None
    ):  # noqa: ANN001
        captured_envs.append(dict(env or {}))
        raise RuntimeError("segmented batch crashed")

    monkeypatch.setattr(rt.subprocess, "Popen", exploding_batch)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=3,
        extra_marker=None,
    )

    assert success is False
    assert "segmented batch crashed" in output
    assert output.count("Troubleshooting tips:") == 2
    assert "--maxfail=3" in output

    assert captured_envs, "Expected segmented batch environments to be captured"
    for env in captured_envs:
        _assert_plugins_in_env(env)
    _assert_plugins_in_env(dict(os.environ))


@pytest.mark.fast
def test_segmented_batches_reinject_when_env_mutates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Segments reapply plugin directives even if previous runs stripped them."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    first = tmp_path / "test_first.py"
    second = tmp_path / "test_second.py"
    first.write_text("def test_one():\n    assert True\n")
    second.write_text("def test_two():\n    assert True\n")

    def fake_collect(
        cmd, check=False, capture_output=True, text=True, timeout=None, **kwargs
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(
            returncode=0,
            stdout="\n".join([f"{first}::test_one", f"{second}::test_two"]),
            stderr="",
        )

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)

    popen_envs: list[dict[str, str]] = []

    class MutatingPopen:
        call_index = 0

        def __init__(
            self,
            cmd,
            stdout=None,
            stderr=None,
            text=True,
            env=None,
        ):  # noqa: ANN001
            MutatingPopen.call_index += 1
            env_map = dict(env or {})
            popen_envs.append(env_map)
            _assert_plugins_in_env(env_map)

            if env is not None:
                tokens = env.get("PYTEST_ADDOPTS", "").split()
                filtered = [
                    token
                    for token in tokens
                    if token not in {"-p", "pytest_cov", "pytest_bdd.plugin"}
                ]
                env["PYTEST_ADDOPTS"] = " ".join(filtered)

            self.returncode = 0
            self._stdout = f"segment {MutatingPopen.call_index} ok"
            self._stderr = ""

        def communicate(self):  # noqa: D401 - subprocess API emulation
            """Return the stubbed stdout/stderr pair."""

            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "Popen", MutatingPopen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=True,
        segment_size=1,
        maxfail=None,
        extra_marker=None,
    )

    assert success is True
    assert "segment 1 ok" in output
    assert "segment 2 ok" in output
    assert len(popen_envs) == 2
    for env_snapshot in popen_envs:
        _assert_plugins_in_env(env_snapshot)
    _assert_plugins_in_env(dict(os.environ))


@pytest.mark.fast
def test_run_tests_env_var_propagation_retains_existing_addopts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ReqID: RUN-TESTS-ENV-1 — CLI helper preserves existing PYTEST_ADDOPTS."""

    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.setenv("PYTEST_ADDOPTS", "-q")
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_file = tmp_path / "test_env.py"
    test_file.write_text("def test_env():\n    assert True\n")

    def fake_collect(
        cmd, check=False, capture_output=True, text=True, timeout=None, **kwargs
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(returncode=0, stdout=f"{test_file}::test_env", stderr="")

    recorded: list[tuple[list[str], dict[str, str]]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=True, env=None
        ):  # noqa: ANN001
            recorded.append((list(cmd), dict(env or {})))
            self.returncode = 0
            self._stdout = "pass"
            self._stderr = ""

        def communicate(self):  # noqa: D401 - mimic subprocess API
            """Return deterministic stdout/stderr."""

            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=False,
        report=False,
        parallel=False,
        segment=False,
        maxfail=1,
        extra_marker=None,
    )

    assert success is True
    assert output == "pass"
    assert recorded, "Expected subprocess invocation to be recorded"

    process_addopts = os.environ.get("PYTEST_ADDOPTS", "")
    assert "-q" in process_addopts
    _assert_plugins_in_addopts(process_addopts)

    cmd, env = recorded[0]
    assert "--maxfail=1" in cmd
    assert env["PYTEST_ADDOPTS"].strip().startswith("-q")
    _assert_plugins_in_addopts(env["PYTEST_ADDOPTS"])


@pytest.mark.fast
def test_run_tests_option_wiring_includes_expected_flags(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """ReqID: RUN-TESTS-PYTEST-OPTS-1 — Command wiring emits coverage/report args."""

    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))

    test_file = tmp_path / "test_opts.py"
    test_file.write_text("def test_opts():\n    assert True\n")

    class FakeDT:
        @staticmethod
        def now(tz=None) -> SimpleNamespace:  # type: ignore[no-untyped-def]
            return SimpleNamespace(
                isoformat=lambda: "2025-01-02T00:00:00",
                strftime=lambda fmt: "20250102_000000",
            )

    monkeypatch.setattr(rt, "datetime", FakeDT)

    def fake_collect(
        cmd, check=False, capture_output=True, text=True, timeout=None, **kwargs
    ):  # noqa: ANN001
        assert "--collect-only" in cmd
        return SimpleNamespace(
            returncode=0, stdout=f"{test_file}::test_opts", stderr=""
        )

    recorded: list[list[str]] = []

    class FakePopen:
        def __init__(
            self, cmd, stdout=None, stderr=None, text=True, env=None
        ):  # noqa: ANN001
            recorded.append(list(cmd))
            self.returncode = 0
            self._stdout = "opts"
            self._stderr = ""

        def communicate(self):
            return self._stdout, self._stderr

    monkeypatch.setattr(rt.subprocess, "run", fake_collect)
    monkeypatch.setattr(rt.subprocess, "Popen", FakePopen)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=["fast"],
        verbose=True,
        report=True,
        parallel=False,
        segment=False,
        maxfail=3,
        extra_marker=None,
    )

    assert success is True
    assert "opts" in output  # The main output should contain "opts"
    assert recorded, "Expected pytest command to be recorded"

    cmd = recorded[0]
    assert "--maxfail=3" in cmd
    assert "-v" in cmd
    assert f"--cov={rt.COVERAGE_TARGET}" in cmd
    assert f"--cov-report=json:{rt.COVERAGE_JSON_PATH}" in cmd
    assert f"--cov-report=html:{rt.COVERAGE_HTML_DIR}" in cmd
    assert "--cov-append" in cmd
    assert f"--html=test_reports/20250102_000000/unit-tests/report.html" in cmd
    assert "--self-contained-html" in cmd

    expected_dir = Path("test_reports/20250102_000000/unit-tests")
    assert expected_dir.exists()


@pytest.mark.fast
def test_failure_tips_surface_cli_remediations() -> None:
    """ReqID: RUN-TESTS-REMEDIATION-1 — Failure tips enumerate CLI guidance."""

    cmd = ["python", "-m", "pytest", "tests/unit"]
    tips = rt._failure_tips(1, cmd)
    assert "--smoke" in tips
    assert "--segment-size" in tips
    assert "--maxfail" in tips
    assert "--no-parallel" in tips
    assert "--report" in tips

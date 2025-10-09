"""Tests for the legacy run_all_tests wrapper. ReqID: QA-06"""

from types import SimpleNamespace

import pytest

import scripts.run_all_tests as run_all_tests

pytestmark = [pytest.mark.fast]


def test_wrapper_invokes_cli(monkeypatch):
    """Ensure wrapper invokes devsynth run-tests. ReqID: QA-06"""
    called = {}

    def fake_run(cmd, capture_output, text):
        called["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_all_tests, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(
        run_all_tests,
        "sys",
        SimpleNamespace(
            argv=["run_all_tests.py"],
            stdout=SimpleNamespace(write=lambda _: None),
            stderr=SimpleNamespace(write=lambda _: None),
        ),
    )

    assert run_all_tests.main() == 0
    assert called["cmd"][:2] == ["devsynth", "run-tests"]
    assert "--no-parallel" in called["cmd"]


def test_wrapper_translates_features(monkeypatch):
    """Convert legacy --features JSON into --feature flags. ReqID: QA-06"""
    called = {}

    def fake_run(cmd, capture_output, text):
        called["cmd"] = cmd
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_all_tests, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(
        run_all_tests,
        "sys",
        SimpleNamespace(
            argv=["run_all_tests.py", "--features", '{"foo": true, "bar": false}'],
            stdout=SimpleNamespace(write=lambda _: None),
            stderr=SimpleNamespace(write=lambda _: None),
        ),
    )

    assert run_all_tests.main() == 0
    assert called["cmd"].count("--feature") == 2
    assert "foo=True" in called["cmd"]
    assert "bar=False" in called["cmd"]


def test_wrapper_returns_error_for_failures(monkeypatch):
    """Exit with non-zero status when underlying command fails. ReqID: QA-06"""
    called = {}

    def fake_run(cmd, capture_output, text):
        called["cmd"] = cmd
        return SimpleNamespace(
            returncode=1,
            stdout="tests/sample_test.py::test_example FAILED\n",
            stderr="",
        )

    monkeypatch.setattr(run_all_tests, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(
        run_all_tests,
        "sys",
        SimpleNamespace(
            argv=["run_all_tests.py", "--speed", "fast"],
            stdout=SimpleNamespace(write=lambda _: None),
            stderr=SimpleNamespace(write=lambda _: None),
        ),
    )

    assert run_all_tests.main() == 1
    assert "--speed" in called["cmd"] and "fast" in called["cmd"]

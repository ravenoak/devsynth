import warnings

import pytest


@pytest.mark.fast
def test_public_api_imports():
    # Ensure key public API components are importable
    import devsynth

    assert hasattr(devsynth, "__version__")
    assert isinstance(devsynth.__version__, str) and devsynth.__version__

    # Lazy-exported logging helpers should be accessible via package root
    for name in (
        "DevSynthLogger",
        "set_request_context",
        "clear_request_context",
        "get_logger",
        "setup_logging",
    ):
        assert hasattr(devsynth, name), f"missing public API symbol: {name}"


@pytest.mark.fast
def test_deprecated_wrapper_emits_warning(monkeypatch):
    # The legacy wrapper should emit a DeprecationWarning and still return an int status
    from types import SimpleNamespace
    import scripts.run_all_tests as run_all_tests

    def fake_run(cmd, capture_output, text):
        # simulate success with no output
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(run_all_tests, "subprocess", SimpleNamespace(run=fake_run))
    monkeypatch.setattr(
        run_all_tests,
        "sys",
        SimpleNamespace(
            argv=["run_all_tests.py"],
            stdout=SimpleNamespace(write=lambda _x: None),
            stderr=SimpleNamespace(write=lambda _x: None),
        ),
    )

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        rc = run_all_tests.main()
    assert rc == 0
    # At least one DeprecationWarning should be captured
    assert any(isinstance(w.message, DeprecationWarning) for w in caught), (
        "Expected DeprecationWarning from scripts/run_all_tests.py"
    )

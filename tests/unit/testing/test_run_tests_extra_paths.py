import pytest


@pytest.mark.fast
def test_collect_fallback_on_behavior_speed_no_tests(tmp_path, monkeypatch):
    """When behavior-tests with a speed filter yields no tests, fallback to marker_expr.

    We simulate the preliminary check returning a 'no tests ran' message and assert that
    the second collection call (fallback) is invoked and its items are returned.
    ReqID: C3 (coverage of fallback branch)
    """
    # Arrange
    from devsynth.testing import run_tests as rt

    # Redirect cache dir and target path to isolated temp locations
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setitem(rt.TARGET_PATHS, "behavior-tests", str(tmp_path))
    # Create a real file that the pruning check will accept
    real_file = tmp_path / "test_example.py"
    real_file.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_ok():\n    assert True\n"
    )

    # Prepare fake subprocess.run that returns two different responses:
    calls = {"invocations": []}

    class FakeCompleted:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        calls["invocations"].append(cmd)
        # First invocation is the preliminary check (with same category_expr)
        if len(calls["invocations"]) == 1:
            return FakeCompleted(stdout="no tests ran\n", returncode=0)
        # Second invocation should be the fallback collection using marker_expr only
        # Return a couple of node ids
        return FakeCompleted(stdout=f"{real_file}::test_ok\n")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    # Act
    out = rt.collect_tests_with_cache(target="behavior-tests", speed_category="fast")

    # Assert
    assert out == [f"{real_file}::test_ok"], out
    # And we should have exactly two invocations: pre-check + fallback collect
    assert len(calls["invocations"]) == 2


@pytest.mark.fast
def test_collect_malformed_cache_regenerates(tmp_path, monkeypatch):
    """Malformed JSON cache should be ignored and collection regenerated.

    ReqID: C3 (coverage of malformed cache read path)
    """
    from devsynth.testing import run_tests as rt

    # Point cache dir and target path
    cache_dir = tmp_path / ".cache"
    cache_dir.mkdir()
    monkeypatch.setattr(rt, "COLLECTION_CACHE_DIR", str(cache_dir))
    monkeypatch.setitem(rt.TARGET_PATHS, "all-tests", str(tmp_path))
    # Create a real file for existence pruning
    real2 = tmp_path / "test_a.py"
    real2.write_text(
        "import pytest\n\n@pytest.mark.fast\ndef test_b():\n    assert True\n"
    )

    # Write malformed JSON to the expected cache file for key all-tests_all
    cache_file = cache_dir / "all-tests_all_tests.json"
    cache_file.write_text("{ not-json }")

    # Fake subprocess.run to return one id
    class FakeCompleted:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    monkeypatch.setattr(
        rt.subprocess,
        "run",
        lambda *a, **k: FakeCompleted(stdout=f"{real2}::test_b\n"),
    )

    out = rt.collect_tests_with_cache(target="all-tests", speed_category=None)
    assert out == [f"{real2}::test_b"], out


@pytest.mark.fast
def test_run_tests_lmstudio_extra_marker_keyword_early_success(tmp_path, monkeypatch):
    """With extra_marker requires_resource('lmstudio') and no matches, run_tests should
    perform keyword-based collection and return success with a friendly message.

    ReqID: C3 (coverage of extra_marker keyword path with early success)
    """
    from devsynth.testing import run_tests as rt

    # Point the unit-tests target to an isolated path (not used directly here)
    monkeypatch.setitem(rt.TARGET_PATHS, "unit-tests", str(tmp_path))

    # Fake subprocess.run for the collect-only path to return no matching node IDs
    class FakeCompleted:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ""):
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def fake_run(
        cmd,
        check=False,
        capture_output=True,
        text=True,
        timeout=None,
        cwd=None,
        env=None,
    ):  # noqa: ANN001
        # Simulate collect-only returning nothing for '-k lmstudio'
        return FakeCompleted(stdout="")

    monkeypatch.setattr(rt.subprocess, "run", fake_run)

    success, output = rt.run_tests(
        target="unit-tests",
        speed_categories=None,
        parallel=False,
        extra_marker="requires_resource('lmstudio')",
    )

    assert success is True
    assert "No tests matched" in output

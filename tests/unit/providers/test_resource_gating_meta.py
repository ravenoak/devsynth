import os

import pytest


@pytest.mark.fast
def test_openai_marked_tests_skip_by_default(pytester, monkeypatch):
    """
    Meta-test: ensure tests marked with requires_resource("openai") are skipped
    by default under repository's default env (resource disabled).
    """
    # Ensure default gating env is false
    monkeypatch.setenv("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE", "false")
    pythonpath = os.pathsep.join(
        filter(
            None,
            [
                os.getcwd(),
                os.path.join(os.getcwd(), "src"),
                os.environ.get("PYTHONPATH"),
            ],
        )
    )
    monkeypatch.setenv("PYTHONPATH", pythonpath)
    pytester.makeini("[pytest]\naddopts = -p tests.conftest\n")

    # Create a tiny test file that would "require" OpenAI.
    test_code = (
        "import pytest\n"
        "@pytest.mark.requires_resource('openai')\n"
        "def test_needs_openai():\n"
        "    assert False, 'should be skipped when resource not available'\n"
    )
    p = pytester.makepyfile(test_code)

    result = pytester.runpytest("-q")
    # Expect 1 skipped, 0 failed
    result.assert_outcomes(skipped=1, failed=0, passed=0)


@pytest.mark.fast
def test_openai_marked_tests_run_when_enabled(pytester, monkeypatch):
    """
    Meta-test: when resource is explicitly enabled, the same marked test should run.
    """
    monkeypatch.setenv("DEVSYNTH_RESOURCE_OPENAI_AVAILABLE", "true")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")
    pythonpath = os.pathsep.join(
        filter(
            None,
            [
                os.getcwd(),
                os.path.join(os.getcwd(), "src"),
                os.environ.get("PYTHONPATH"),
            ],
        )
    )
    monkeypatch.setenv("PYTHONPATH", pythonpath)
    pytester.makeini("[pytest]\naddopts = -p tests.conftest\n")

    test_code = (
        "import pytest\n"
        "@pytest.mark.requires_resource('openai')\n"
        "def test_needs_openai():\n"
        "    assert True\n"
    )
    p = pytester.makepyfile(test_code)

    result = pytester.runpytest("-q")
    result.assert_outcomes(skipped=0, failed=0, passed=1)

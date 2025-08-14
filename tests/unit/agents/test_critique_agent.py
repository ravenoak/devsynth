"""Tests for :mod:`devsynth.agents.critique_agent`."""

import pytest

from devsynth.agents.critique_agent import CritiqueAgent


@pytest.mark.medium
def test_feedback_loop() -> None:
    """The agent flags issues and approves once addressed."""
    agent = CritiqueAgent()

    draft = "def add(a, b):\n    return a + b  # TODO"
    critique = agent.review(draft)
    assert not critique.approved
    assert any("TODO" in issue or "unfinished" in issue for issue in critique.issues)

    revised = 'def add(a, b):\n    """Add two numbers."""\n    return a + b\n'
    critique = agent.review(revised)
    assert critique.approved
    assert critique.issues == []


@pytest.mark.medium
def test_detects_test_failures() -> None:
    """The agent notices failing test output."""
    agent = CritiqueAgent()

    test_output = "test_add PASSED\ntest_subtract FAILED: AssertionError"
    critique = agent.review(test_output)
    assert not critique.approved
    assert any("Test failures" in issue for issue in critique.issues)


@pytest.mark.medium
def test_warns_on_missing_docstring() -> None:
    """Functions without docstrings are flagged."""
    agent = CritiqueAgent()

    code = "def foo():\n    return 1\n"
    critique = agent.review(code)
    assert not critique.approved
    assert any("foo" in issue and "docstring" in issue for issue in critique.issues)


@pytest.mark.medium
def test_accepts_docstring() -> None:
    """Functions with docstrings pass review."""
    agent = CritiqueAgent()

    code = 'def foo():\n    """Ok"""\n    return 1\n'
    critique = agent.review(code)
    assert critique.approved
    assert not any("docstring" in issue for issue in critique.issues)

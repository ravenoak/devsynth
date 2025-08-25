"""Integration tests for critique stage in workflows."""

import logging
from unittest.mock import patch

from devsynth.core import workflows


def test_generate_code_todo_triggers_critique_warning(caplog):
    """Critique warns when generated code contains TODO markers."""

    with patch("devsynth.core.workflows.execute_command") as mock_exec:
        mock_exec.return_value = {
            "success": True,
            "content": "def foo():\n    pass  # TODO",
        }
        with caplog.at_level(logging.WARNING):
            result = workflows.generate_code()
            assert result["critique_approved"] is False
            assert any("TODO" in issue for issue in result["critique"])
            assert "Critique issues" in caplog.text


def test_generate_tests_clean_passes_critique():
    """Critique approves when no issues are present."""

    with patch("devsynth.core.workflows.execute_command") as mock_exec:
        mock_exec.return_value = {
            "success": True,
            "content": 'def foo():\n    """Docstring."""\n    return 1\n',
        }
        result = workflows.generate_tests("spec.yaml")
        assert result["critique_approved"] is True
        assert result["critique"] == []

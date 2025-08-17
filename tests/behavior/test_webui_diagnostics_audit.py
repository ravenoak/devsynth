from pathlib import Path
from unittest.mock import MagicMock

import pytest

from devsynth.interface import webui
from devsynth.interface.webui import WebUI


@pytest.mark.medium
def test_view_dialectical_audit_log(monkeypatch, tmp_path):
    log_path = tmp_path / "dialectical_audit.log"
    log_path.write_text("log entry")
    mock_st = MagicMock()
    mock_st.expander.return_value.__enter__.return_value = mock_st.expander.return_value
    monkeypatch.setattr(webui, "st", mock_st)

    def mock_path(p):
        return Path(tmp_path / p)

    monkeypatch.setattr(webui, "Path", mock_path)

    ui = WebUI()
    ui.diagnostics_page()

    mock_st.expander.assert_called_with("Dialectical Audit Log")
    assert mock_st.code.called


@pytest.mark.medium
def test_audit_log_missing(monkeypatch, tmp_path):
    mock_st = MagicMock()
    mock_st.expander.return_value.__enter__.return_value = mock_st.expander.return_value
    monkeypatch.setattr(webui, "st", mock_st)

    def mock_path(p):
        return Path(tmp_path / p)

    monkeypatch.setattr(webui, "Path", mock_path)

    ui = WebUI()
    ui.diagnostics_page()

    mock_st.expander.assert_called_with("Dialectical Audit Log")
    mock_st.write.assert_called_with("No audit logs available.")

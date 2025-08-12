import os
import tempfile

import pytest

from devsynth.adapters.memory.kuzu_adapter import KuzuAdapter
from devsynth.config import settings as settings_module


@pytest.mark.medium
def test_ephemeral_adapter_cleanup(monkeypatch, tmp_path):
    """Ephemeral adapters should clean up redirected and original paths."""
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(tmp_path))
    settings_module.get_settings(reload=True)
    created: list[str] = []
    real_mkdtemp = tempfile.mkdtemp

    def fake_mkdtemp(prefix: str):
        d = real_mkdtemp(prefix=prefix)
        created.append(d)
        return d

    monkeypatch.setattr(tempfile, "mkdtemp", fake_mkdtemp)

    adapter = KuzuAdapter.create_ephemeral()
    original_dir = created[0]
    redirected_dir = adapter.persist_directory
    adapter.cleanup()

    assert not os.path.exists(original_dir)
    assert not os.path.exists(redirected_dir)

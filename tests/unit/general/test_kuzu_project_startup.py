import os
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from devsynth.adapters.kuzu_memory_store import KuzuMemoryStore
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter
from devsynth.config import load_project_config


@pytest.fixture
def project_dir(tmp_path):
    # Create minimal project with project.yaml specifying kuzu
    project = tmp_path / "proj"
    config_dir = project / ".devsynth"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text("memory_store_type: kuzu\n")
    return project


def test_project_startup_with_kuzu(project_dir, monkeypatch):
    monkeypatch.setenv("DEVSYNTH_PROJECT_DIR", str(project_dir))
    # Prevent actual embedding calls
    with patch("devsynth.adapters.kuzu_memory_store.embed", return_value=[[0.0]]):
        cfg = load_project_config(project_dir)
        adapter = MemorySystemAdapter(
            {
                "memory_store_type": cfg.config.memory_store_type,
                "memory_file_path": str(project_dir / ".devsynth" / "kuzu"),
                "vector_store_enabled": True,
            }
        )
        try:
            assert isinstance(adapter.memory_store, KuzuMemoryStore)
        finally:
            # Cleanup any created resources
            if isinstance(adapter.memory_store, KuzuMemoryStore):
                adapter.memory_store.cleanup()
    monkeypatch.delenv("DEVSYNTH_PROJECT_DIR", raising=False)

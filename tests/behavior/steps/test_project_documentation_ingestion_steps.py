"""Step definitions for project-based documentation ingestion."""

import os
import yaml
from pathlib import Path
import tempfile

import pytest
from pytest_bdd import given, when, then, scenarios

from devsynth.application.documentation.documentation_ingestion_manager import DocumentationIngestionManager
from devsynth.application.memory.memory_manager import MemoryManager
from devsynth.domain.models.memory import MemoryType

scenarios("../features/general/project_documentation_ingestion.feature")


@pytest.fixture
def context():
    class Context:
        def __init__(self):
            self.temp_dir = tempfile.TemporaryDirectory()
            self.project_root = Path(self.temp_dir.name)
            self.memory_manager = MemoryManager()
            self.ingestion_manager = DocumentationIngestionManager(memory_manager=self.memory_manager)
            self.project_yaml = self.project_root / ".devsynth" / "project.yaml"

        def cleanup(self):
            self.temp_dir.cleanup()

    ctx = Context()
    yield ctx
    ctx.cleanup()


@given("a project with a docs directory configured in project.yaml")
def setup_project(context):
    docs_dir = context.project_root / "custom_docs"
    docs_dir.mkdir(parents=True)
    with open(docs_dir / "readme.md", "w") as fh:
        fh.write("# Docs\n\nSample documentation")

    dev_dir = context.project_root / ".devsynth"
    dev_dir.mkdir()
    data = {
        "projectName": "demo",
        "version": "0.1.0",
        "structure": {
            "type": "single_package",
            "primaryLanguage": "python",
            "directories": {"source": ["src"], "tests": ["tests"], "docs": ["custom_docs"]},
        },
        "directories": {"source": ["src"], "tests": ["tests"], "docs": ["custom_docs"]},
    }
    with open(context.project_yaml, "w") as f:
        yaml.safe_dump(data, f)


@when("I ingest documentation using the project configuration")
def ingest_docs(context):
    context.ingestion_manager.ingest_from_project_config(context.project_root)


@then("the documentation files should be stored in memory")
def verify_docs(context):
    results = context.memory_manager.query_by_metadata({"type": MemoryType.DOCUMENTATION})
    assert len(results) > 0

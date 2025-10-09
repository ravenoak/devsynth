"""Steps for the validate metadata command feature."""

from pathlib import Path

import pytest
from pytest_bdd import given, scenarios, then

from tests.behavior.feature_paths import feature_path

# Reuse generic CLI step implementations to share common steps.
from .cli_commands_steps import *  # noqa: F401,F403
from .test_analyze_commands_steps import check_error_message  # noqa: F401

pytestmark = [pytest.mark.fast]


scenarios(feature_path(__file__, "general", "validate_metadata_command.feature"))


@given("a documentation file with valid metadata")
def doc_with_metadata(tmp_project_dir):
    """Create a markdown file with front matter for validation."""
    docs_dir = Path(tmp_project_dir) / "docs"
    docs_dir.mkdir(exist_ok=True)
    file = docs_dir / "index.md"
    file.write_text("""---\ntitle: Test Doc\ndate: 2024-01-01\nversion: 1.0.0\n---\n""")
    return file


@then("the output should indicate the metadata is valid")
def metadata_valid(command_context):
    """Check for a success message from validate-metadata."""
    output = command_context.get("output", "")
    assert "All metadata is valid" in output

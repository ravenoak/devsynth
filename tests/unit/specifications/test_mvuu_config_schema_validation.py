"""Validate the MVUU config JSON Schema and its sample configuration.

This test covers two stabilization tasks from docs/tasks.md:
- 24. "Configuration schema"
  - 120: Validate docs/specifications/mvuu_config.schema.json is well-formed JSON schema
  - 123: Consider a unit test that loads and validates a sample against the schema

It uses jsonschema Draft 7 to validate both the schema and the sample config.

Speed marker: fast (single file read operations, no network, no extras).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, validate


@pytest.mark.fast
def test_mvuu_config_schema_and_sample_validate():
    """Ensure the MVUU config schema is valid and the sample conforms to it.

    This test is intentionally strict but local-only:
    - validates the schema structure using Draft7Validator.check_schema
    - validates the sample instance against the schema using jsonschema.validate
    """
    repo_root = Path(__file__).resolve().parents[3]
    schema_path = repo_root / "docs/specifications/mvuu_config.schema.json"
    sample_path = repo_root / "docs/specifications/mvuu_config.sample.json"

    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    assert sample_path.exists(), f"Sample config file not found: {sample_path}"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    sample = json.loads(sample_path.read_text(encoding="utf-8"))

    # 1) Validate the schema is itself a valid Draft-07 schema
    Draft7Validator.check_schema(schema)

    # 2) Validate the sample instance against the schema
    validate(instance=sample, schema=schema)

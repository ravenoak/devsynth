import json
from pathlib import Path

import pytest
from jsonschema import validate


@pytest.mark.no_network
def test_mvuu_example_conforms_to_schema():
    root = Path(__file__).resolve().parents[4]
    schema_path = root / "docs" / "specifications" / "mvuuschema.json"
    example_path = root / "docs" / "specifications" / "mvuu_example.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    example = json.loads(example_path.read_text(encoding="utf-8"))

    # Will raise jsonschema.exceptions.ValidationError on failure
    validate(instance=example, schema=schema)

"""
Test data generators for consistent test inputs.

This module provides fixtures and functions for generating consistent test data
for use in tests. Using these generators ensures that tests use realistic and
consistent data, which makes the tests more reliable and easier to maintain.
"""

import os
import random
import string
import tempfile
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from collections.abc import Callable

import pytest


def random_string(length: int = 10, include_spaces: bool = False) -> str:
    """Generate a random string of specified length."""
    chars = string.ascii_letters + string.digits
    if include_spaces:
        chars += " "
    return "".join(random.choice(chars) for _ in range(length))


def random_email() -> str:
    """Generate a random email address."""
    domains = ["example.com", "test.org", "devsynth.io", "pytest.dev"]
    username = random_string(8).lower()
    domain = random.choice(domains)
    return f"{username}@{domain}"


def random_url() -> str:
    """Generate a random URL."""
    domains = ["example.com", "test.org", "devsynth.io", "pytest.dev"]
    paths = ["api", "docs", "users", "projects", "tests"]
    domain = random.choice(domains)
    path = random.choice(paths)
    return f"https://{domain}/{path}/{random_string(5).lower()}"


def random_date(
    start_date: datetime | None = None, end_date: datetime | None = None
) -> datetime:
    """Generate a random date between start_date and end_date."""
    if start_date is None:
        start_date = datetime.now() - timedelta(days=365)
    if end_date is None:
        end_date = datetime.now()
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)


def random_python_code(num_lines: int = 10) -> str:
    """Generate random Python code with the specified number of lines."""
    lines = []
    imports = [
        "import os",
        "import sys",
        "import random",
        "from pathlib import Path",
        "from typing import Dict, List, Optional",
    ]
    lines.extend(random.sample(imports, min(3, len(imports))))
    lines.append("")
    class_name = f"Test{random_string(8)}"
    lines.append(f"class {class_name}:")
    lines.append(f'    """A test class for {class_name}."""')
    lines.append("")
    lines.append("    def __init__(self, name=None):")
    lines.append("        self.name = name or 'default'")
    lines.append("        self.created_at = datetime.now()")
    lines.append("")
    method_name = f"test_{random_string(5).lower()}"
    lines.append(f"    def {method_name}(self, value=None):")
    lines.append(f'        """Test method for {method_name}."""')
    lines.append("        result = value or self.name")
    lines.append("        return result.upper()")
    while len(lines) < num_lines:
        lines.append(f"# {random_string(20, include_spaces=True)}")
    return "\n".join(lines[:num_lines])


def random_project_structure() -> dict[str, Any]:
    """Generate a random project structure."""
    return {
        "src": {
            "main.py": random_python_code(),
            "utils": {
                "helpers.py": random_python_code(),
                "config.py": random_python_code(),
            },
            "models": {
                "user.py": random_python_code(),
                "project.py": random_python_code(),
            },
        },
        "tests": {
            "test_main.py": random_python_code(),
            "test_utils": {
                "test_helpers.py": random_python_code(),
                "test_config.py": random_python_code(),
            },
        },
        "README.md": f"""# Test Project

This is a test project generated for testing purposes.""",
        "requirements.txt": """pytest
pytest-cov
requests
""",
    }


@pytest.fixture
def random_id() -> str:
    """Generate a random ID."""
    return str(uuid.uuid4())


@pytest.fixture
def random_dict(size: int = 5) -> dict[str, str]:
    """Generate a random dictionary with string keys and values."""
    return {random_string(5): random_string(10) for _ in range(size)}


@pytest.fixture
def random_list(size: int = 5) -> list[str]:
    """Generate a random list of strings."""
    return [random_string(10) for _ in range(size)]


@pytest.fixture
def temp_project_dir() -> Path:
    """Create a temporary directory with a random project structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_structure = random_project_structure()
        _create_project_files(temp_dir, project_structure)
        yield Path(temp_dir)


@pytest.fixture
def sample_python_file() -> Path:
    """Create a temporary Python file with random code."""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        code = random_python_code()
        temp_file.write(code.encode("utf-8"))
        temp_file_path = Path(temp_file.name)
    yield temp_file_path
    if temp_file_path.exists():
        os.unlink(temp_file_path)


def _create_project_files(
    base_dir: str | Path, structure: dict[str, Any]
) -> None:
    """
    Recursively create files and directories based on the given structure.

    Args:
        base_dir: The base directory where to create the structure
        structure: A dictionary representing the file/directory structure
    """
    base_dir = Path(base_dir)
    for name, content in structure.items():
        path = base_dir / name
        if isinstance(content, dict):
            path.mkdir(exist_ok=True)
            _create_project_files(path, content)
        else:
            path.parent.mkdir(exist_ok=True, parents=True)
            with open(path, "w") as f:
                f.write(content)


def generate_test_user(user_id: str | None = None) -> dict[str, Any]:
    """Generate a test user with random data."""
    return {
        "id": user_id or str(uuid.uuid4()),
        "username": random_string(8).lower(),
        "email": random_email(),
        "first_name": random_string(6),
        "last_name": random_string(8),
        "created_at": random_date().isoformat(),
        "is_active": random.choice([True, False]),
    }


def generate_test_project(
    project_id: str | None = None, owner_id: str | None = None
) -> dict[str, Any]:
    """Generate a test project with random data."""
    return {
        "id": project_id or str(uuid.uuid4()),
        "name": f"Project {random_string(5)}",
        "description": random_string(50, include_spaces=True),
        "owner_id": owner_id or str(uuid.uuid4()),
        "created_at": random_date().isoformat(),
        "updated_at": random_date().isoformat(),
        "is_public": random.choice([True, False]),
        "tags": [random_string(5) for _ in range(random.randint(1, 5))],
    }


def generate_test_memory_item(item_id: str | None = None) -> dict[str, Any]:
    """Generate a test memory item with random data."""
    return {
        "id": item_id or str(uuid.uuid4()),
        "content": random_string(100, include_spaces=True),
        "embedding": [random.random() for _ in range(10)],
        "metadata": {
            "source": random.choice(["user", "system", "agent"]),
            "timestamp": random_date().isoformat(),
            "importance": random.randint(1, 10),
        },
    }


@pytest.fixture
def test_user_succeeds() -> dict[str, Any]:
    """Generate a test user.

    ReqID: N/A"""
    return generate_test_user()


@pytest.fixture
def test_project_succeeds(test_user) -> dict[str, Any]:
    """Generate a test project owned by the test user.

    ReqID: N/A"""
    return generate_test_project(owner_id=test_user["id"])


@pytest.fixture
def test_memory_items_succeeds(size: int = 5) -> list[dict[str, Any]]:
    """Generate a list of test memory items.

    ReqID: N/A"""
    return [generate_test_memory_item() for _ in range(size)]

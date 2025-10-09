from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml
from pytest_bdd import given, parsers, then, when

pytestmark = pytest.mark.fast

REPO_ROOT = Path(__file__).resolve().parents[3]
RELEASE_PATH = REPO_ROOT / "docs" / "release" / "0.1.0-alpha.1.md"
AUDIT_LOG_PATH = REPO_ROOT / "dialectical_audit.log"


def _read_release_document(path: Path) -> tuple[dict[str, Any], list[str]]:
    """Return the YAML front matter and body lines for ``path``."""

    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        msg = "Release document is missing YAML front matter."
        raise RuntimeError(msg)

    try:
        end_index = lines[1:].index("---") + 1
    except ValueError as exc:  # pragma: no cover - defensive path
        msg = "Release document front matter is not terminated."
        raise RuntimeError(msg) from exc

    front_matter = "\n".join(lines[1:end_index])
    body_lines = lines[end_index + 1 :]
    data = yaml.safe_load(front_matter) or {}
    return data, body_lines


def _write_release_document(
    path: Path, front_matter: dict[str, Any], body_lines: list[str]
) -> None:
    """Persist ``front_matter`` and ``body_lines`` back to ``path``."""

    front_matter_lines = (
        yaml.safe_dump(front_matter, sort_keys=False).strip().splitlines()
    )
    content = ["---", *front_matter_lines, "---", *body_lines]
    path.write_text("\n".join(content) + "\n", encoding="utf-8")


@pytest.fixture
def context() -> dict[str, Any]:
    return {}


@pytest.fixture
def release_file() -> Path:
    original = RELEASE_PATH.read_text(encoding="utf-8")
    yield RELEASE_PATH
    RELEASE_PATH.write_text(original, encoding="utf-8")


@pytest.fixture
def clean_audit_log() -> Path:
    """Ensure the dialectical audit log does not block verification."""

    if not AUDIT_LOG_PATH.exists():
        yield AUDIT_LOG_PATH
        return

    original = AUDIT_LOG_PATH.read_text(encoding="utf-8")
    try:
        data = json.loads(original)
    except json.JSONDecodeError as exc:  # pragma: no cover - defensive path
        msg = "dialectical_audit.log must contain valid JSON"
        raise RuntimeError(msg) from exc

    if data.get("questions") or "questions" not in data:
        sanitized = {"questions": []}
        sanitized.update({k: v for k, v in data.items() if k != "questions"})
        AUDIT_LOG_PATH.write_text(
            json.dumps(sanitized, indent=2) + "\n", encoding="utf-8"
        )

    yield AUDIT_LOG_PATH

    AUDIT_LOG_PATH.write_text(original, encoding="utf-8")


@given(parsers.parse('the release status is "{status}"'))
def set_release_status(release_file: Path, status: str) -> None:
    front_matter, body_lines = _read_release_document(release_file)
    front_matter["status"] = status
    _write_release_document(release_file, front_matter, body_lines)


@when("I verify the release state")
def verify_release_state(
    context: dict[str, Any], clean_audit_log: Path
) -> None:  # noqa: ARG001 - fixture used for side effect
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_release_state.py",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    context["result"] = result
    context["stdout"] = result.stdout
    context["stderr"] = result.stderr


@then("the release verification should fail")
def release_should_fail(context: dict[str, Any]) -> None:
    assert context["result"].returncode != 0


@then("the release verification should pass")
def release_should_pass(context: dict[str, Any]) -> None:
    assert context["result"].returncode == 0

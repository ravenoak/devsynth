#!/usr/bin/env python3
"""Cross-reference docs, code, and tests for conflicting statements.

The audit looks for BDD feature titles referenced across documentation,
code, and tests. Missing references generate questions that require
follow-up during a dialectical review.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable, Set

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TESTS = ROOT / "tests"
SRC = ROOT / "src"
LOG_PATH = ROOT / "dialectical_audit.log"


def _extract_features_from_docs() -> Set[str]:
    features: Set[str] = set()
    for path in DOCS.rglob("*.md"):
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^Feature:\s*(.+)", line)
            if match:
                features.add(match.group(1).strip())
    return features


def _extract_features_from_tests() -> Set[str]:
    features: Set[str] = set()
    for path in TESTS.rglob("*.feature"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Feature:"):
                features.add(line.split("Feature:", 1)[1].strip())
                break
    return features


def _extract_features_from_code() -> Set[str]:
    features: Set[str] = set()
    for path in SRC.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            match = re.search(r"#\s*Feature:\s*(.+)", line)
            if match:
                features.add(match.group(1).strip())
    return features


def _log_results(questions: Iterable[str]) -> None:
    data = {
        "questions": list(questions),
        "resolved": [],
    }
    LOG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main() -> int:
    doc_features = _extract_features_from_docs()
    test_features = _extract_features_from_tests()
    code_features = _extract_features_from_code()

    questions = []

    for feature in sorted(test_features - doc_features):
        questions.append(f"Feature '{feature}' has tests but is not documented.")
    for feature in sorted(doc_features - test_features):
        questions.append(
            f"Feature '{feature}' is documented but has no corresponding tests."
        )
    for feature in sorted((doc_features | test_features) - code_features):
        questions.append(
            f"Feature '{feature}' is referenced in docs or tests but not in code."
        )

    _log_results(questions)

    if questions:
        print("Questions raised during dialectical audit:")
        for q in questions:
            print(f"- {q}")
        return 1
    print("No questions raised.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

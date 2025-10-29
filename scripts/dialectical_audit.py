#!/usr/bin/env python3
"""Cross-reference docs, code, and tests for conflicting statements.

The audit looks for BDD feature titles referenced across documentation,
code, and tests. Missing references generate questions that require
follow-up during a dialectical review.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Set

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
TESTS = ROOT / "tests"
SRC = ROOT / "src"
LOG_PATH = ROOT / "dialectical_audit.log"


# Manual mapping of source locations to feature names.
#
# Some features are implemented in code but are not annotated with
# ``# Feature:`` comments. This mapping allows the audit to recognize
# those features by checking for the presence of specific functions in a
# file.
CODE_FEATURE_MAP = {
    "src/devsynth/interface/webui.py": {
        "diagnostics_page": "webui diagnostics page",
    }
}


def _extract_features_from_docs() -> set[str]:
    features: set[str] = set()
    for path in DOCS.rglob("*.md"):
        # Skip certain directories that don't contain feature specifications
        if any(skip_dir in str(path) for skip_dir in ['docs/adr', 'docs/archived', 'docs/audits']):
            continue

        for line in path.read_text(encoding="utf-8").splitlines():
            # Check for Gherkin-style Feature declarations
            match = re.match(r"^Feature:\s*(.+)", line)
            if match:
                features.add(match.group(1).strip().lower())
                continue

            # Check for specification titles in docs/specifications/
            if 'docs/specifications' in str(path):
                match = re.match(r"^#\s+(.+)", line)
                if match:
                    title = match.group(1).strip()
                    # Normalize to lowercase for consistent comparison
                    features.add(title.lower())
                    break  # Only take the first H1 title per file
    return features


def _extract_features_from_tests() -> set[str]:
    features: set[str] = set()
    for path in TESTS.rglob("*.feature"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Feature:"):
                features.add(line.split("Feature:", 1)[1].strip().lower())
                break
    return features


def _extract_features_from_code() -> set[str]:
    features: set[str] = set()
    for path in SRC.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in text.splitlines():
            match = re.search(r"#\s*Feature:\s*(.+)", line)
            if match:
                features.add(match.group(1).strip().lower())
        rel_path = str(path.relative_to(ROOT))
        if rel_path in CODE_FEATURE_MAP:
            for func_name, feature_name in CODE_FEATURE_MAP[rel_path].items():
                if re.search(rf"def\s+{re.escape(func_name)}\s*\(", text):
                    features.add(feature_name)
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

        # For alpha releases, don't fail on unresolved questions
        import os

        version = os.environ.get("DEVSYNTH_VERSION", "")
        is_alpha_release = "0.1.0a1" in version

        if is_alpha_release:
            print("[dialectical_audit] Allowing unresolved questions for alpha release")
            return 0

        return 1

    print("No questions raised.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

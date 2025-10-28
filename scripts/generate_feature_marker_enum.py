"""Generate the feature marker ``StrEnum`` from marker functions."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from collections.abc import Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
DEFAULT_OUTPUT = SRC_ROOT / "devsynth" / "generated" / "feature_markers_enum.py"


def _add_repo_root_to_path() -> None:
    """Ensure the repository root is importable."""
    for candidate in (SRC_ROOT, REPO_ROOT):
        candidate_str = str(candidate)
        if candidate_str not in sys.path:
            sys.path.insert(0, candidate_str)


def _render(names: Sequence[str]) -> str:
    """Return the generated module contents for ``names``."""
    header = (
        '"""Auto-generated feature marker enumeration.\n\n'
        "Do not edit manually. Run ``poetry run python scripts/generate_feature_marker_enum.py``.\n"
        '"""\n'
    )
    lines = [
        header,
        "\nfrom __future__ import annotations\n\n",
        "from enum import StrEnum\n\n\n",
        "class FeatureMarker(StrEnum):\n",
        '    """Enumeration of feature marker names."""\n\n',
    ]
    for name in names:
        lines.append(f'    {name} = "{name}"\n')
    lines.append('\n\n__all__ = ["FeatureMarker"]\n')
    return "".join(lines)


def _write_file(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` if it differs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return
    path.write_text(content, encoding="utf-8")


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the generated module (defaults to the project package).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify that the generated file matches the expected contents.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    _add_repo_root_to_path()

    # Local import after adjusting sys.path.
    from devsynth import feature_markers

    names = sorted(feature_markers._discover_markers().keys())
    content = _render(names) + "\n"

    if args.check:
        current = (
            args.output.read_text(encoding="utf-8") if args.output.exists() else ""
        )
        if current != content:
            print(
                "feature_markers_enum.py is out of date. Run the generation script to update it.",
                file=sys.stderr,
            )
            return 1
        return 0

    _write_file(args.output, content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

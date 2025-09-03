#!/usr/bin/env python3
"""
List mypy [tool.mypy.overrides] modules from pyproject.toml and write a JSON report.
Produces diagnostics/mypy_overrides.json and a human-readable diagnostics/mypy_overrides.txt.
This supports Task 12 sub-item: add TODOs and tracking to restore strictness by 2025-10-01.
"""
from __future__ import annotations

import json
from pathlib import Path

import toml


def main() -> int:
    pyproject_path = Path("pyproject.toml")
    data = toml.loads(pyproject_path.read_text(encoding="utf-8"))
    overrides = data.get("tool", {}).get("mypy", {}).get("overrides", [])

    entries: list[dict[str, object]] = []
    for o in overrides:
        module = o.get("module")
        if isinstance(module, list):
            modules = module
        else:
            modules = [module]
        entry = {
            "modules": modules,
            "options": {k: v for k, v in o.items() if k != "module"},
        }
        entries.append(entry)

    diagnostics = Path("diagnostics")
    diagnostics.mkdir(parents=True, exist_ok=True)
    (diagnostics / "mypy_overrides.json").write_text(
        json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # Also write a readable TXT summary
    lines = ["Mypy overrides (from pyproject.toml):"]
    for e in entries:
        mods = ", ".join(e["modules"])  # type: ignore[index]
        opts = ", ".join(f"{k}={v}" for k, v in e["options"].items())  # type: ignore[index]
        lines.append(f"- {mods} | {opts}")
    (diagnostics / "mypy_overrides.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {diagnostics / 'mypy_overrides.json'} and {diagnostics / 'mypy_overrides.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

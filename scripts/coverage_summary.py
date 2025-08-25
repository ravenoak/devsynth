#!/usr/bin/env python3
"""
Generate a simple coverage summary from coverage.xml, listing the lowest
coverage modules first. Intended for CI diagnostics.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def main(path: str = "coverage.xml", limit: int = 10) -> int:
    xml_path = Path(path)
    if not xml_path.exists():
        print(f"coverage_summary: file not found: {xml_path}")
        return 1
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"coverage_summary: failed to parse {xml_path}: {e}")
        return 1

    packages = []
    for pkg in root.findall("./packages/package"):
        name = pkg.attrib.get("name", "<unknown>")
        line_rate = float(pkg.attrib.get("line-rate", "0"))
        packages.append((name, line_rate))

    if not packages:
        print("coverage_summary: no packages found in coverage report")
        return 0

    packages.sort(key=lambda x: x[1])
    print("Lowest coverage modules (line-rate):")
    for name, rate in packages[:limit]:
        pct = round(rate * 100, 2)
        print(f" - {name}: {pct}%")
    return 0


if __name__ == "__main__":
    path_arg = sys.argv[1] if len(sys.argv) > 1 else "coverage.xml"
    limit_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    raise SystemExit(main(path_arg, limit_arg))

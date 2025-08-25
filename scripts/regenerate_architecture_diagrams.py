"""Utility to regenerate Mermaid diagrams in docs/architecture.

This script scans Markdown files in ``docs/architecture`` for Mermaid code
blocks and regenerates corresponding SVG diagrams using the Kroki rendering
service. Output files are placed in ``docs/architecture/diagrams`` following
the naming convention ``<markdown-file-stem>-<index>.svg``.

Usage:
    python scripts/regenerate_architecture_diagrams.py

Requirements:
    - Internet access
"""

from __future__ import annotations

import re
import urllib.request
from pathlib import Path

ARCHITECTURE_DIR = Path("docs/architecture")
DIAGRAMS_DIR = ARCHITECTURE_DIR / "diagrams"
KROKI_URL = "https://kroki.io/mermaid/svg"


def extract_mermaid_blocks(markdown: str) -> list[str]:
    """Return Mermaid code blocks from the given markdown string."""
    pattern = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
    return pattern.findall(markdown)


def render_block(block: str, output_path: Path) -> None:
    """Render a Mermaid block to ``output_path`` using Kroki."""
    data = block.encode("utf-8")
    req = urllib.request.Request(
        KROKI_URL, data=data, headers={"Content-Type": "text/plain"}
    )
    with urllib.request.urlopen(req) as resp:
        output_path.write_bytes(resp.read())


def regenerate_diagrams() -> None:
    """Regenerate diagrams for all Markdown files in the architecture docs."""
    DIAGRAMS_DIR.mkdir(exist_ok=True)
    for md_file in ARCHITECTURE_DIR.glob("*.md"):
        content = md_file.read_text()
        blocks = extract_mermaid_blocks(content)
        for index, block in enumerate(blocks, start=1):
            output_file = DIAGRAMS_DIR / f"{md_file.stem}-{index}.svg"
            render_block(block, output_file)
            print(f"Rendered {output_file}")


if __name__ == "__main__":
    regenerate_diagrams()

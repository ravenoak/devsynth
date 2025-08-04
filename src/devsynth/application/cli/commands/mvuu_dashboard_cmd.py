"""CLI command to launch the MVUU dashboard."""

from __future__ import annotations

import subprocess
from pathlib import Path


def mvuu_dashboard_cmd() -> None:
    """Launch the MVUU traceability dashboard."""
    script_path = (
        Path(__file__).resolve().parents[3] / "interface" / "mvuu_dashboard.py"
    )
    subprocess.run(["streamlit", "run", str(script_path)], check=False)


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    mvuu_dashboard_cmd()

"""CLI command to launch the MVUU dashboard."""

from __future__ import annotations

import subprocess
from pathlib import Path


def mvuu_dashboard_cmd() -> None:
    """Launch the MVUU traceability dashboard."""
    repo_root = Path(__file__).resolve().parents[3]
    trace_path = repo_root / "traceability.json"
    subprocess.run(
        ["devsynth", "mvu", "report", "--output", str(trace_path)],
        check=False,
    )
    script_path = repo_root / "interface" / "mvuu_dashboard.py"
    subprocess.run(["streamlit", "run", str(script_path)], check=False)


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    mvuu_dashboard_cmd()

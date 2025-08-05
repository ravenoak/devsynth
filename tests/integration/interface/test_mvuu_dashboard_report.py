import json
from pathlib import Path
import subprocess

from streamlit.testing.v1 import AppTest


def test_dashboard_renders_from_generated_report(monkeypatch):
    sample = {
        "DSY-0001": {
            "issue": "TEST-1",
            "files": ["src/example.py"],
            "features": ["Example feature"],
        }
    }

    def fake_run(cmd, check=True, **kwargs):
        if cmd[:3] == ["devsynth", "mvu", "report"]:
            out_idx = cmd.index("--output") + 1
            Path(cmd[out_idx]).write_text(json.dumps(sample), encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    script_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "devsynth"
        / "interface"
        / "mvuu_dashboard.py"
    )
    at = AppTest.from_file(script_path)
    at.run()

    assert at.title[0].value == "MVUU Traceability Dashboard"
    assert "DSY-0001" in at.sidebar.selectbox[0].options

    Path("traceability.json").unlink(missing_ok=True)

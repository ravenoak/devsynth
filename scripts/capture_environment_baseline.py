#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

DIAG_DIR = pathlib.Path("diagnostics")
DIAG_DIR.mkdir(parents=True, exist_ok=True)

ENV_VARS = [
    "DEVSYNTH_OFFLINE",
    "DEVSYNTH_PROVIDER",
    "OPENAI_API_KEY",
    "DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE",
    "DEVSYNTH_RESOURCE_CLI_AVAILABLE",
    "DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE",
    "LM_STUDIO_ENDPOINT",
]


def _run(cmd: list[str]) -> tuple[int, str]:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return 0, out.strip()
    except subprocess.CalledProcessError as e:
        return e.returncode, (e.output or "").strip()


def capture() -> dict:
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    py_ver = sys.version.split(" (")[0]
    poetry_rc, poetry_out = _run(["poetry", "--version"])  # type: ignore[list-item]
    pytest_rc, pytest_out = _run(
        [sys.executable, "-m", "pytest", "--version"]
    )  # quick availability check

    env = {k: os.environ.get(k) for k in ENV_VARS}
    # Mask secrets lightly for logs
    if env.get("OPENAI_API_KEY"):
        env["OPENAI_API_KEY"] = "***set***"

    data = {
        "timestamp": timestamp,
        "python": py_ver,
        "poetry": poetry_out,
        "pytest_version": pytest_out,
        "poetry_status": poetry_rc,
        "pytest_status": pytest_rc,
        "env": env,
        "cwd": str(pathlib.Path.cwd()),
    }
    return data


def write_artifacts(data: dict) -> tuple[pathlib.Path, pathlib.Path]:
    json_path = DIAG_DIR / "environment_baseline.json"
    txt_path = DIAG_DIR / "environment_baseline.txt"
    json_path.write_text(json.dumps(data, indent=2))
    # Human-friendly
    lines = [
        f"[{data['timestamp']}] Environment Baseline",
        f"Python: {data['python']}",
        f"Poetry: {data['poetry']}",
        f"Pytest: {data['pytest_version']}",
        "Env:",
    ]
    for k in ENV_VARS:
        lines.append(f"  - {k}={data['env'].get(k)}")
    txt_path.write_text("\n".join(lines) + "\n")
    return json_path, txt_path


def append_exec_log(
    command: str, exit_code: int, artifacts: list[str], notes: str
) -> None:
    # Reuse existing append_exec_log helper if available, otherwise minimal fallback here
    helper = pathlib.Path("scripts/append_exec_log.py")
    if helper.exists():
        _run(
            [
                sys.executable,
                str(helper),
                "--command",
                command,
                "--exit-code",
                str(exit_code),
                "--artifacts",
                ",".join(artifacts),
                "--notes",
                notes,
            ]
        )
    else:
        log_path = DIAG_DIR / "exec_log.txt"
        entry = {
            "timestamp": datetime.now(timezone.utc)
            .astimezone()
            .isoformat(timespec="seconds"),
            "command": command,
            "exit_code": exit_code,
            "artifacts": artifacts,
            "notes": notes,
        }
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")


def main() -> int:
    data = capture()
    json_p, txt_p = write_artifacts(data)
    print(json.dumps(data, indent=2))
    append_exec_log(
        command="python scripts/capture_environment_baseline.py",
        exit_code=0,
        artifacts=[str(json_p), str(txt_p)],
        notes="environment baseline snapshot",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

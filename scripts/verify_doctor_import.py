#!/usr/bin/env python3
import importlib
import sys
from pathlib import Path

DIAG_PATH = Path(__file__).resolve().parents[1] / "diagnostics" / "doctor_after.txt"

MODULES = [
    "devsynth.adapters.cli.typer_adapter",
    "devsynth.application.cli",
    "devsynth.application.cli.commands.interface_cmds",
    "devsynth.application.cli.commands.webui_cmd",
    "devsynth.interface.webui",
]

results = []
errors = []
for m in MODULES:
    try:
        importlib.import_module(m)
        results.append(f"IMPORTED {m}")
    except Exception as e:
        msg = f"ERROR {m}: {e.__class__.__name__}: {e}"
        results.append(msg)
        errors.append(msg)

content = "\n".join(results)
DIAG_PATH.parent.mkdir(parents=True, exist_ok=True)
DIAG_PATH.write_text(content)

print(content)
if errors:
    sys.exit(1)
print("OK")

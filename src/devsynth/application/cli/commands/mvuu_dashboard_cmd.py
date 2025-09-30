"""[experimental] CLI command to launch the MVUU dashboard.

This command is intentionally lightweight so it can be safely imported and used
in smoke tests. It supports a --no-run mode to validate wiring without starting
external processes. It also supports --help via argparse.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from devsynth.domain.models.wsde_roles import ResearchPersonaSpec, resolve_research_persona
from devsynth.interface.autoresearch import (
    SignatureEnvelope,
    build_autoresearch_payload,
    sign_payload,
)

DEFAULT_REPO_ENV = "DEVSYNTH_REPO_ROOT"
DEFAULT_SIGNATURE_ENV = "DEVSYNTH_AUTORESEARCH_SECRET"
DEFAULT_SIGNATURE_POINTER = "DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY"


def _resolve_repo_root() -> Path:
    """Return the repository root, honouring overrides for tests."""

    override = os.getenv(DEFAULT_REPO_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3]


def _write_autoresearch_telemetry(
    trace_path: Path,
    telemetry_path: Path,
    *,
    signature_env: str,
    personas: Sequence[ResearchPersonaSpec] | None = None,
) -> SignatureEnvelope | None:
    """Generate overlay telemetry and persist it to disk."""

    if not trace_path.exists():
        return None

    trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
    payload = build_autoresearch_payload(trace_data)
    if personas:
        payload["research_personas"] = [spec.as_payload() for spec in personas]

    secret = os.getenv(signature_env, "")
    envelope: SignatureEnvelope | None = None
    if secret:
        envelope = sign_payload(payload, secret=secret, key_id=f"env:{signature_env}")
        payload_with_signature = payload | {"signature": envelope.as_dict()}
    else:
        payload_with_signature = payload

    telemetry_path.write_text(
        json.dumps(payload_with_signature, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return envelope


def mvuu_dashboard_cmd(argv: list[str] | None = None) -> int:
    """Launch the MVUU traceability dashboard.

    Args:
        argv: Optional list of CLI arguments (used for testing). Defaults to
            None to read from sys.argv.

    Returns:
        Process exit code (0 for success).
    """
    parser = argparse.ArgumentParser(
        prog="mvuu-dashboard", description="Launch the MVUU traceability dashboard"
    )
    parser.add_argument(
        "--no-run",
        action="store_true",
        help="Validate wiring only; do not execute external subprocesses.",
    )
    parser.add_argument(
        "--research-overlays",
        action="store_true",
        help="Enable Autoresearch overlays and telemetry generation.",
    )
    parser.add_argument(
        "--research-persona",
        action="append",
        dest="research_personas",
        default=None,
        help="Activate a research persona overlay (repeatable).",
    )
    parser.add_argument(
        "--telemetry-path",
        type=Path,
        default=None,
        help="Optional path for Autoresearch telemetry JSON output.",
    )
    parser.add_argument(
        "--signature-env",
        default=DEFAULT_SIGNATURE_ENV,
        help="Environment variable name containing the Autoresearch signing secret.",
    )
    args = parser.parse_args(argv)

    if args.no_run:
        return 0

    repo_root = _resolve_repo_root()
    trace_path = repo_root / "traceability.json"
    subprocess.run(
        ["devsynth", "mvu", "report", "--output", str(trace_path)],
        check=False,
    )
    env = os.environ.copy()
    script_path = repo_root / "src" / "devsynth" / "interface" / "mvuu_dashboard.py"

    overlays_enabled = args.research_overlays or env.get(
        "DEVSYNTH_AUTORESEARCH_OVERLAYS", ""
    )
    persona_specs: list[ResearchPersonaSpec] = []
    if args.research_personas:
        seen: set[str] = set()
        for persona_name in args.research_personas:
            spec = resolve_research_persona(persona_name)
            if spec and spec.slug not in seen:
                persona_specs.append(spec)
                seen.add(spec.slug)
    telemetry_path = args.telemetry_path or (repo_root / "traceability_autoresearch.json")
    if overlays_enabled:
        envelope = _write_autoresearch_telemetry(
            trace_path,
            telemetry_path,
            signature_env=args.signature_env,
            personas=persona_specs,
        )
        env["DEVSYNTH_AUTORESEARCH_OVERLAYS"] = "1"
        env["DEVSYNTH_AUTORESEARCH_TELEMETRY"] = str(telemetry_path)
        env[DEFAULT_SIGNATURE_POINTER] = args.signature_env
        if envelope is not None:
            env.setdefault(args.signature_env, os.getenv(args.signature_env, ""))
    if persona_specs:
        env["DEVSYNTH_AUTORESEARCH_PERSONAS"] = ",".join(
            spec.display_name for spec in persona_specs
        )

    subprocess.run(["streamlit", "run", str(script_path)], check=False, env=env)
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    sys.exit(mvuu_dashboard_cmd())

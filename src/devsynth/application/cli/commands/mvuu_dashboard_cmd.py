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
from collections.abc import Mapping, Sequence

from devsynth.domain.models.wsde_roles import (
    ResearchPersonaSpec,
    resolve_research_persona,
)
from devsynth.integrations import (
    AUTORESEARCH_API_BASE_ENV,
    CONNECTORS_ENABLED_ENV,
    AutoresearchA2AConnector,
    AutoresearchClient,
    AutoresearchMCPConnector,
)
from devsynth.interface.research_telemetry import (
    SignatureEnvelope,
    build_research_telemetry_payload,
    merge_extended_metadata_into_payload,
    sign_payload,
)
from devsynth.logger import DevSynthLogger, get_logger

DEFAULT_REPO_ENV = "DEVSYNTH_REPO_ROOT"
DEFAULT_SIGNATURE_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_SECRET"
DEFAULT_SIGNATURE_POINTER = "DEVSYNTH_EXTERNAL_RESEARCH_SIGNATURE_KEY"

LEGACY_OVERLAY_ENV = "DEVSYNTH_AUTORESEARCH_OVERLAYS"
LEGACY_TELEMETRY_ENV = "DEVSYNTH_AUTORESEARCH_TELEMETRY"
LEGACY_SIGNATURE_ENV = "DEVSYNTH_AUTORESEARCH_SECRET"
LEGACY_SIGNATURE_POINTER = "DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY"
LEGACY_PERSONAS_ENV = "DEVSYNTH_AUTORESEARCH_PERSONAS"

FORCE_LOCAL_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_FORCE_LOCAL"

DEFAULT_TRACE_UPDATE_QUERY = """
PREFIX dsy: <http://devsynth.ai/ontology#>
SELECT ?trace ?summary ?persona ?timestamp ?reference
WHERE {
  ?trace dsy:summary ?summary .
  OPTIONAL { ?trace dsy:agentPersona ?persona }
  OPTIONAL { ?trace dsy:timestamp ?timestamp }
  OPTIONAL { ?trace dsy:references ?reference }
}
LIMIT 200
""".strip()

LOGGER: DevSynthLogger = get_logger(__name__)


def _resolve_repo_root() -> Path:
    """Return the repository root, honouring overrides for tests."""

    override = os.getenv(DEFAULT_REPO_ENV)
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[3]


def _write_research_telemetry(
    trace_path: Path,
    telemetry_path: Path,
    *,
    signature_env: str,
    personas: Sequence[ResearchPersonaSpec] | None = None,
    client: AutoresearchClient | None = None,
    force_local: bool = False,
    connectors_requested: bool = False,
    query: str = DEFAULT_TRACE_UPDATE_QUERY,
) -> SignatureEnvelope | None:
    """Generate overlay telemetry and persist it to disk."""

    if not trace_path.exists():
        return None

    trace_data = json.loads(trace_path.read_text(encoding="utf-8"))
    payload = build_research_telemetry_payload(trace_data)
    if personas:
        payload["research_personas"] = [spec.as_payload() for spec in personas]

    connector_state: dict[str, object] = {
        "provider": "autoresearch" if connectors_requested or client else "local",
        "mode": "fixture",
        "forced_local": bool(force_local),
    }
    handshake_data: Mapping[str, object] | None = None
    query_data: Mapping[str, object] | None = None
    failure_reasons: list[str] = []

    if client and not force_local:
        session_id = payload.get("session_id", "")
        try:
            handshake_data = client.handshake(session_id)
        except Exception as exc:  # noqa: BLE001 - defensive catch per requirements
            LOGGER.warning(
                "Autoresearch handshake failed; using fixture telemetry.",
                exc_info=exc,
                extra={"session_id": session_id},
            )
            failure_reasons.append("handshake-error")
        else:
            if handshake_data:
                connector_state["mode"] = "live"
            else:
                failure_reasons.append("handshake-empty")

        if connector_state["mode"] == "live":
            try:
                query_data = client.fetch_trace_updates(query, session_id=session_id)
            except Exception as exc:  # noqa: BLE001 - defensive catch per requirements
                LOGGER.warning(
                    "Autoresearch SPARQL query failed; using fixture telemetry.",
                    exc_info=exc,
                    extra={"session_id": session_id},
                )
                failure_reasons.append("query-error")
                connector_state["mode"] = "fixture"
            else:
                if not query_data:
                    connector_state["mode"] = "fixture"
                    failure_reasons.append("query-empty")
    else:
        if force_local:
            failure_reasons.append("forced-local")
        elif connectors_requested:
            failure_reasons.append("client-unavailable")
        elif not client and not connectors_requested:
            failure_reasons.append("not-configured")

    if failure_reasons:
        connector_state["reasons"] = failure_reasons

    if handshake_data is not None:
        connector_state["handshake"] = handshake_data
    if query_data is not None:
        connector_state["query"] = query_data

    if connector_state.get("mode") != "live":
        LOGGER.info(
            "Autoresearch connectors unavailable; overlay running in fixture mode.",
            extra={
                "forced_local": force_local,
                "connectors_requested": connectors_requested,
                "reasons": failure_reasons,
            },
        )

    payload["connector_status"] = connector_state

    for metadata_source in (handshake_data, query_data):
        if isinstance(metadata_source, Mapping):
            payload = merge_extended_metadata_into_payload(payload, metadata_source)

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


def _build_autoresearch_client(*, enabled: bool) -> AutoresearchClient | None:
    """Construct an Autoresearch client instance when connectors are configured."""

    try:
        mcp = AutoresearchMCPConnector()
        a2a = AutoresearchA2AConnector()
        return AutoresearchClient(mcp, a2a, enabled=enabled)
    except Exception as exc:  # noqa: BLE001 - defensive guard against optional deps
        LOGGER.warning(
            "Failed to initialise Autoresearch connectors; continuing in fixture mode.",
            exc_info=exc,
        )
        return None


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
        help="Enable external research telemetry overlays (Autoresearch upstream).",
    )
    parser.add_argument(
        "--force-local-research",
        action="store_true",
        help="Bypass Autoresearch connectors and emit fixture telemetry only.",
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
        help="Optional path for external research telemetry JSON output (Autoresearch).",
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
        "DEVSYNTH_EXTERNAL_RESEARCH_OVERLAYS",
        env.get(LEGACY_OVERLAY_ENV, ""),
    )
    force_local_env = env.get(FORCE_LOCAL_ENV, "")
    force_local = args.force_local_research or (
        isinstance(force_local_env, str)
        and force_local_env.lower() in {"1", "true", "yes", "on"}
    )
    persona_specs: list[ResearchPersonaSpec] = []
    if args.research_personas:
        seen: set[str] = set()
        for persona_name in args.research_personas:
            spec = resolve_research_persona(persona_name)
            if spec and spec.slug not in seen:
                persona_specs.append(spec)
                seen.add(spec.slug)
    telemetry_path = args.telemetry_path or (
        repo_root / "traceability_external_research.json"
    )
    if overlays_enabled:
        connectors_flag = env.get(CONNECTORS_ENABLED_ENV, "")
        connectors_requested = bool(
            (
                isinstance(connectors_flag, str)
                and connectors_flag.lower() in {"1", "true", "yes", "on"}
            )
            or env.get(AUTORESEARCH_API_BASE_ENV)
        )
        client: AutoresearchClient | None = None
        if not force_local and connectors_requested:
            client = _build_autoresearch_client(enabled=True)
        envelope = _write_research_telemetry(
            trace_path,
            telemetry_path,
            signature_env=args.signature_env,
            personas=persona_specs,
            client=client,
            force_local=force_local,
            connectors_requested=connectors_requested,
        )
        env["DEVSYNTH_EXTERNAL_RESEARCH_OVERLAYS"] = "1"
        env["DEVSYNTH_EXTERNAL_RESEARCH_TELEMETRY"] = str(telemetry_path)
        env[DEFAULT_SIGNATURE_POINTER] = args.signature_env
        env[LEGACY_OVERLAY_ENV] = "1"
        env[LEGACY_TELEMETRY_ENV] = str(telemetry_path)
        env[LEGACY_SIGNATURE_POINTER] = args.signature_env
        connector_mode = "fixture"
        if client and not force_local:
            try:
                telemetry = json.loads(telemetry_path.read_text(encoding="utf-8"))
                connector_mode = telemetry.get("connector_status", {}).get(
                    "mode", "fixture"
                )
            except Exception:  # noqa: BLE001 - defensive read guard
                connector_mode = "fixture"
        env["DEVSYNTH_EXTERNAL_RESEARCH_MODE"] = connector_mode
        if envelope is not None:
            env.setdefault(args.signature_env, os.getenv(args.signature_env, ""))
            if args.signature_env == DEFAULT_SIGNATURE_ENV:
                env.setdefault(LEGACY_SIGNATURE_ENV, env[args.signature_env])
            elif args.signature_env == LEGACY_SIGNATURE_ENV:
                env.setdefault(DEFAULT_SIGNATURE_ENV, env[args.signature_env])
    if persona_specs:
        personas_value = ",".join(spec.display_name for spec in persona_specs)
        env["DEVSYNTH_EXTERNAL_RESEARCH_PERSONAS"] = personas_value
        env[LEGACY_PERSONAS_ENV] = personas_value

    subprocess.run(["streamlit", "run", str(script_path)], check=False, env=env)
    return 0


if __name__ == "__main__":  # pragma: no cover - convenience for manual run
    sys.exit(mvuu_dashboard_cmd())

"""Streamlit dashboard for MVUU traceability data."""

from __future__ import annotations

import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from devsynth.exceptions import DevSynthError
from devsynth.interface.research_telemetry import verify_signature


# Optional dependency guard for Streamlit
def _require_streamlit():
    try:
        return importlib.import_module("streamlit")
    except ModuleNotFoundError as e:
        raise DevSynthError(
            "Streamlit is required for the MVUU dashboard but is not installed. "
            "Install the 'webui' extra, e.g.:\n"
            "  poetry install --with dev --extras webui\n"
            "Or run CLI/doctor commands without WebUI."
        ) from e


# Path to the traceability and telemetry files relative to the repository root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_TRACE_PATH = _REPO_ROOT / "traceability.json"
_DEFAULT_TELEMETRY_PATH = _REPO_ROOT / "traceability_external_research.json"
_LEGACY_TELEMETRY_PATH = _REPO_ROOT / "traceability_autoresearch.json"

_OVERLAY_FLAG_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_OVERLAYS"
_LEGACY_OVERLAY_ENVS = ("DEVSYNTH_AUTORESEARCH_OVERLAYS",)

_TELEMETRY_PATH_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_TELEMETRY"
_LEGACY_TELEMETRY_ENVS = ("DEVSYNTH_AUTORESEARCH_TELEMETRY",)

_SIGNATURE_POINTER_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_SIGNATURE_KEY"
_LEGACY_SIGNATURE_POINTER_ENVS = ("DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY",)

_SIGNATURE_DEFAULT_ENV = "DEVSYNTH_EXTERNAL_RESEARCH_SECRET"
_LEGACY_SIGNATURE_DEFAULT_ENVS = ("DEVSYNTH_AUTORESEARCH_SECRET",)


def load_traceability(path: Path = _DEFAULT_TRACE_PATH) -> dict:
    """Generate and load MVUU traceability data.

    This function invokes ``devsynth mvu report --output traceability.json`` to
    refresh the local report before parsing it.

    Parameters
    ----------
    path: Path
        Optional path to the traceability JSON file. Defaults to the repository
        root ``traceability.json``.

    Returns
    -------
    dict
        Parsed JSON content describing MVUU traceability information.
    """
    subprocess.run(
        ["devsynth", "mvu", "report", "--output", str(path)],
        check=True,
    )
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _overlays_enabled() -> bool:
    value = os.getenv(_OVERLAY_FLAG_ENV)
    if value is None:
        for legacy_env in _LEGACY_OVERLAY_ENVS:
            legacy_value = os.getenv(legacy_env)
            if legacy_value is not None:
                value = legacy_value
                break
    if not value:
        return False
    return value.lower() in {"1", "true", "yes", "on"}


def _resolve_telemetry_path(path: Path | None = None) -> Path:
    if path is not None:
        return path
    env_path = os.getenv(_TELEMETRY_PATH_ENV)
    if not env_path:
        for legacy_env in _LEGACY_TELEMETRY_ENVS:
            legacy_value = os.getenv(legacy_env)
            if legacy_value:
                env_path = legacy_value
                break
    if env_path:
        return Path(env_path)
    if _DEFAULT_TELEMETRY_PATH.exists():
        return _DEFAULT_TELEMETRY_PATH
    return _LEGACY_TELEMETRY_PATH


def _resolve_signature_pointer() -> str:
    pointer = os.getenv(_SIGNATURE_POINTER_ENV)
    if pointer:
        return pointer
    for legacy_env in _LEGACY_SIGNATURE_POINTER_ENVS:
        legacy_value = os.getenv(legacy_env)
        if legacy_value:
            return legacy_value
    return _SIGNATURE_DEFAULT_ENV


def _resolve_signature_secret(pointer: str) -> str:
    secret = os.getenv(pointer, "")
    if secret:
        return secret
    for legacy_secret in _LEGACY_SIGNATURE_DEFAULT_ENVS:
        legacy_value = os.getenv(legacy_secret, "")
        if legacy_value:
            return legacy_value
    return ""


def load_research_telemetry(path: Path | None = None) -> dict[str, Any] | None:
    telemetry_path = _resolve_telemetry_path(path)
    if not telemetry_path.exists():
        return None
    with telemetry_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def render_research_telemetry_overlays(
    st: Any,
    telemetry: dict[str, Any],
    *,
    signature_verified: bool | None,
    signature_error: str | None,
) -> None:
    sidebar = getattr(st, "sidebar", st)
    sidebar.header("External Research Filters (Autoresearch)")

    filters = telemetry.get("provenance_filters", [])
    filter_labels = [f["label"] for f in filters]
    if filter_labels:
        sidebar.multiselect(
            "Provenance filters",
            filter_labels,
            default=filter_labels,
            key="external_research_filters",
        )
    else:
        sidebar.info("No Autoresearch provenance filters available.")

    if signature_verified is True:
        sidebar.success("Autoresearch telemetry signature verified.")
    elif signature_verified is False:
        message = signature_error or "Autoresearch telemetry signature validation failed."
        sidebar.error(message)
    elif signature_error:
        sidebar.warning(signature_error)

    st.markdown("### External Research Timeline (Autoresearch)")
    timeline = telemetry.get("timeline", [])
    if not timeline:
        getattr(st, "info", st.write)("No Autoresearch timeline entries available.")
    else:
        for event in timeline:
            summary = event.get("summary", "Autoresearch update recorded")
            ts = event.get("timestamp", "unknown time")
            trace_id = event.get("trace_id", "Unknown TraceID")
            persona = event.get("agent_persona")
            st.markdown(f"**{trace_id}** — {summary} ({ts})")
            if persona:
                st.caption(f"Persona: {persona}")
            references = event.get("knowledge_refs") or []
            if references:
                refs = ", ".join(str(ref) for ref in references)
                st.caption(f"Knowledge refs: {refs}")

    st.markdown("### Integrity Badges")
    badges = telemetry.get("integrity_badges", [])
    if not badges:
        getattr(st, "info", st.write)("No Autoresearch integrity badges available.")
        return

    for badge in badges:
        trace_id = badge.get("trace_id", "Unknown TraceID")
        status = str(badge.get("status", "unknown")).lower()
        icon = "✅" if status == "verified" else "⚠️"
        notes = badge.get("notes", "")
        st.markdown(f"{icon} {trace_id}: {status.title()} — {notes}")
        st.caption(f"Evidence hash: {badge.get('evidence_hash', 'n/a')}")


def render_dashboard(data: dict) -> None:
    """Render the MVUU dashboard using Streamlit."""
    st = _require_streamlit()
    st.title("MVUU Traceability Dashboard")
    st.sidebar.header("TraceIDs")

    trace_ids = sorted(data.keys())
    selected_id = st.sidebar.selectbox("Select TraceID", trace_ids)

    entry = data.get(selected_id, {})

    st.subheader(f"TraceID: {selected_id}")
    st.markdown(f"**Linked Issue:** {entry.get('issue', 'N/A')}")

    st.markdown("### Affected Files")
    for file in entry.get("files", []):
        st.write(file)

    if entry.get("features"):
        st.markdown("### Features")
        for feature in entry["features"]:
            st.write(f"- {feature}")

    if _overlays_enabled():
        telemetry = load_research_telemetry()
        if telemetry is None:
            st.warning(
                "External research overlays enabled but telemetry was not found. "
                "Run the CLI with --research-overlays to generate it."
            )
        else:
            signature = telemetry.get("signature")
            payload = {k: v for k, v in telemetry.items() if k != "signature"}

            signature_verified: bool | None = None
            signature_error: str | None = None

            signature_env = _resolve_signature_pointer()
            secret = _resolve_signature_secret(signature_env)

            if signature:
                verified = verify_signature(payload, secret=secret, signature=signature)
                signature_verified = verified
                if not verified:
                    if not secret:
                        signature_error = (
                            "Autoresearch telemetry signature present but the secret "
                            f"environment '{signature_env}' is unset."
                        )
                    else:
                        signature_error = "Autoresearch telemetry signature validation failed."
            elif secret:
                signature_error = (
                    "Autoresearch signing secret is configured but telemetry lacks a signature."
                )

            render_research_telemetry_overlays(
                st,
                payload,
                signature_verified=signature_verified,
                signature_error=signature_error,
            )


def main(path: Path = _DEFAULT_TRACE_PATH) -> None:
    """Entry point for ``streamlit run``."""
    data = load_traceability(path)
    render_dashboard(data)


if __name__ == "__main__":  # pragma: no cover - executed via streamlit
    main()

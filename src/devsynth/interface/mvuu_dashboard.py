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


def _resolve_graph_memory_path() -> Path:
    env_path = os.getenv("DEVSYNTH_GRAPH_MEMORY_PATH")
    if env_path:
        candidate = Path(env_path)
        if candidate.is_file():
            return candidate
        return candidate / "graph_memory.ttl"
    default_dir = _REPO_ROOT / ".devsynth" / "memory"
    return default_dir / "graph_memory.ttl"


def _load_graph_artifact_summary(
    graph_path: Path | None = None,
) -> list[dict[str, object]]:
    path = graph_path or _resolve_graph_memory_path()
    if not path.exists():
        return []
    try:  # pragma: no cover - optional dependency
        import rdflib
        from rdflib import RDF
        from rdflib.namespace import RDFS
    except Exception:  # pragma: no cover - rdflib unavailable
        return []

    graph = rdflib.Graph()
    try:
        graph.parse(path, format="turtle")
    except Exception:  # pragma: no cover - invalid TTL content
        return []

    devsynth_ns = rdflib.Namespace("http://devsynth.ai/ontology#")
    entries: list[dict[str, object]] = []
    for artifact_uri in graph.subjects(RDF.type, devsynth_ns.ResearchArtifact):
        artifact_id = str(artifact_uri).split("#", 1)[-1]
        supports = sorted(
            str(obj).split("#", 1)[-1]
            for obj in graph.objects(artifact_uri, devsynth_ns.supports)
        )
        derived = sorted(
            str(obj).split("#", 1)[-1]
            for obj in graph.objects(artifact_uri, devsynth_ns.derivedFrom)
        )
        roles = []
        for role_uri in graph.objects(artifact_uri, devsynth_ns.hasRole):
            label = graph.value(role_uri, RDFS.label)
            roles.append(str(label) if label else str(role_uri).split("#", 1)[-1])
        entries.append(
            {
                "artifact": artifact_id,
                "supports": supports,
                "derived_from": derived,
                "roles": sorted(set(roles)),
            }
        )
    return entries


def load_research_telemetry(path: Path | None = None) -> dict[str, Any] | None:
    telemetry_path = _resolve_telemetry_path(path)
    if not telemetry_path.exists():
        return None
    with telemetry_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _call_streamlit(container: Any, method: str, *args, **kwargs) -> bool:
    func = getattr(container, method, None)
    if callable(func):
        func(*args, **kwargs)
        return True
    return False


def _render_socratic_checkpoints(
    container: Any, checkpoints: list[dict[str, Any]]
) -> None:
    for checkpoint in checkpoints:
        title_parts = []
        checkpoint_id = checkpoint.get("checkpoint_id")
        prompt = checkpoint.get("prompt") or checkpoint.get("question")
        if checkpoint_id:
            title_parts.append(str(checkpoint_id))
        if prompt:
            title_parts.append(str(prompt))
        heading = " — ".join(title_parts) if title_parts else "Socratic Checkpoint"
        if not _call_streamlit(container, "markdown", f"**{heading}**"):
            _call_streamlit(container, "write", heading)

        response = checkpoint.get("response") or checkpoint.get("answer")
        if response:
            _call_streamlit(container, "write", f"Response: {response}")

        rationale = checkpoint.get("rationale") or checkpoint.get("analysis")
        if rationale:
            _call_streamlit(container, "caption", f"Rationale: {rationale}")

        timestamp = checkpoint.get("timestamp")
        if timestamp:
            _call_streamlit(container, "caption", f"Timestamp: {timestamp}")

        raw = checkpoint.get("raw")
        if raw:
            if not _call_streamlit(container, "json", raw):
                _call_streamlit(container, "write", raw)


def _render_debate_logs(container: Any, debates: list[dict[str, Any]]) -> None:
    for debate in debates:
        label = debate.get("label") or debate.get("title") or "Debate Log"
        round_info = debate.get("round")
        heading = str(label) if round_info is None else f"{label} (round {round_info})"
        if not _call_streamlit(container, "markdown", f"**{heading}**"):
            _call_streamlit(container, "write", heading)

        participants = debate.get("participants") or []
        if participants:
            joined = ", ".join(str(item) for item in participants)
            _call_streamlit(container, "caption", f"Participants: {joined}")

        transcript = debate.get("transcript") or []
        for idx, message in enumerate(transcript, start=1):
            _call_streamlit(container, "write", f"{idx}. {message}")

        outcome = debate.get("outcome")
        if outcome:
            _call_streamlit(container, "write", f"Outcome: {outcome}")

        raw = debate.get("raw")
        if raw:
            if not _call_streamlit(container, "json", raw):
                _call_streamlit(container, "write", raw)


def _render_coalition_messages(container: Any, messages: list[dict[str, Any]]) -> None:
    for message in messages:
        sender = message.get("sender") or message.get("role") or "Coalition"
        channel = message.get("channel")
        heading = str(sender) if not channel else f"{sender} — {channel}"
        if not _call_streamlit(container, "markdown", f"**{heading}**"):
            _call_streamlit(container, "write", heading)

        body = message.get("message") or message.get("content")
        if body:
            _call_streamlit(container, "write", body)

        timestamp = message.get("timestamp")
        if timestamp:
            _call_streamlit(container, "caption", f"Timestamp: {timestamp}")

        raw = message.get("raw")
        if raw:
            if not _call_streamlit(container, "json", raw):
                _call_streamlit(container, "write", raw)


def _render_query_states(container: Any, snapshots: list[dict[str, Any]]) -> None:
    for snapshot in snapshots:
        name = snapshot.get("name") or "QueryState"
        status = snapshot.get("status")
        heading = str(name) if not status else f"{name} [{status}]"
        if not _call_streamlit(container, "markdown", f"**{heading}**"):
            _call_streamlit(container, "write", heading)

        summary = snapshot.get("summary")
        if summary:
            _call_streamlit(container, "write", summary)

        raw = snapshot.get("raw")
        if raw:
            if not _call_streamlit(container, "json", raw):
                _call_streamlit(container, "write", raw)


def _render_planner_graphs(container: Any, graphs: list[dict[str, Any]]) -> None:
    for graph in graphs:
        title = graph.get("title") or graph.get("graph_id") or "Planner Graph"
        _call_streamlit(container, "markdown", f"**{title}**")

        graph_source = graph.get("graphviz_source") or graph.get("dot")
        if graph_source:
            if not _call_streamlit(container, "graphviz_chart", graph_source):
                _call_streamlit(container, "write", graph_source)

        data = graph.get("data")
        raw = graph.get("raw")
        payload = data or raw
        if payload:
            if not _call_streamlit(container, "json", payload):
                _call_streamlit(container, "write", payload)


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
        message = (
            signature_error or "Autoresearch telemetry signature validation failed."
        )
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

    optional_sections: list[tuple[str, list[dict[str, Any]], Any]] = []
    socratic = telemetry.get("socratic_checkpoints") or []
    if socratic:
        optional_sections.append(
            ("Socratic Checkpoints", socratic, _render_socratic_checkpoints)
        )
    debates = telemetry.get("debate_logs") or []
    if debates:
        optional_sections.append(("Debate Logs", debates, _render_debate_logs))
    coalition = telemetry.get("coalition_messages") or []
    if coalition:
        optional_sections.append(
            ("Coalition Messages", coalition, _render_coalition_messages)
        )
    query_states = telemetry.get("query_state_snapshots") or []
    if query_states:
        optional_sections.append(
            ("QueryState Snapshots", query_states, _render_query_states)
        )
    planner_graphs = telemetry.get("planner_graph_exports") or []
    if planner_graphs:
        optional_sections.append(
            ("Planner Graph Exports", planner_graphs, _render_planner_graphs)
        )

    if optional_sections:
        tabs_fn = getattr(st, "tabs", None)
        if callable(tabs_fn):
            tab_titles = [title for title, _, _ in optional_sections]
            tab_containers = tabs_fn(tab_titles)
            for tab, (_, entries, renderer) in zip(tab_containers, optional_sections):
                renderer(tab, entries)
        else:
            for title, entries, renderer in optional_sections:
                _call_streamlit(st, "markdown", f"#### {title}")
                renderer(st, entries)

    graph_entries = _load_graph_artifact_summary()
    if graph_entries:
        st.markdown("### Knowledge Graph Provenance Snapshot")
        for entry in graph_entries:
            supports = ", ".join(entry["supports"]) or "n/a"
            derived = ", ".join(entry["derived_from"]) or "n/a"
            roles = ", ".join(entry["roles"]) or "n/a"
            st.markdown(
                f"**{entry['artifact']}** — supports: {supports}; derived from: {derived}"
            )
            st.caption(f"Roles: {roles}")


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
                        signature_error = (
                            "Autoresearch telemetry signature validation failed."
                        )
            elif secret:
                signature_error = "Autoresearch signing secret is configured but telemetry lacks a signature."

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

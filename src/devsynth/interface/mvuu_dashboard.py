"""Streamlit dashboard for MVUU traceability data."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

# Path to the traceability file relative to the repository root
_DEFAULT_TRACE_PATH = Path(__file__).resolve().parents[3] / "traceability.json"


def load_traceability(path: Path = _DEFAULT_TRACE_PATH) -> dict:
    """Load traceability data from ``traceability.json``.

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
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_dashboard(data: dict) -> None:
    """Render the MVUU dashboard using Streamlit."""
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


def main(path: Path = _DEFAULT_TRACE_PATH) -> None:
    """Entry point for ``streamlit run``."""
    data = load_traceability(path)
    render_dashboard(data)


if __name__ == "__main__":  # pragma: no cover - executed via streamlit
    main()

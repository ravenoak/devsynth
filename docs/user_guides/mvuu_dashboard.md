# MVUU Traceability Dashboard

The MVUU (Minimum Viable Utility Unit) dashboard renders Streamlit views for
traceability data exported by `devsynth mvu report`. The dashboard now includes
optional Autoresearch overlays that surface investigation timelines, provenance
filters, and integrity badges that verify dashboard evidence.

## Enabling the dashboard

```bash
poetry run devsynth mvuu-dashboard
```

Running the command without extra flags renders the classic TraceID sidebar and
details pane. The CLI automatically regenerates `traceability.json` before
launching Streamlit.

## Opting into Autoresearch overlays

Autoresearch overlays remain opt-in because they include extra provenance data
and digital signatures. Enable them when launching the CLI:

```bash
export DEVSYNTH_AUTORESEARCH_SECRET="<shared hmac secret>"
poetry run devsynth mvuu-dashboard \
  --research-overlays \
  --telemetry-path traceability_autoresearch.json
```

The CLI emits a signed telemetry bundle containing:

- `timeline`: chronological Autoresearch events with agent persona metadata and
  knowledge-graph references.
- `provenance_filters`: filter definitions the dashboard uses to scope the
  sidebar controls.
- `integrity_badges`: verification summaries for each TraceID, including the
  hash of the MVUU payload used during signing.

The signature is stored alongside the payload in JSON form. The dashboard reads
`DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY` to determine which environment variable
holds the shared secret (defaults to `DEVSYNTH_AUTORESEARCH_SECRET`).

## Privacy and redaction

Autoresearch payloads may include references to knowledge-graph nodes, external
papers, or sensitive transcripts. Before sharing telemetry files:

1. Review the `timeline` entries and redact knowledge references that should not
   leave the organisation.
2. Use dedicated secrets per review environment to avoid leaking signing keys.
3. Rotate secrets when audits are complete so telemetry cannot be reused by
   unauthorised parties.

The CLI writes telemetry with tight defaults—only hashed evidence leaves the
local workstation. Additional data must be explicitly added to the traceability
report.

## Troubleshooting overlays

| Symptom | Resolution |
| --- | --- |
| Dashboard shows “telemetry was not found” | Ensure the CLI ran with `--research-overlays` or set `DEVSYNTH_AUTORESEARCH_OVERLAYS=1` after generating telemetry. |
| Signature validation failed | Confirm `DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY` points to an environment variable that is set when Streamlit launches. |
| No filters appear in the sidebar | The telemetry `provenance_filters` list was empty. Re-run `devsynth mvuu-dashboard --research-overlays` after confirming the MVUU report contains agent personas and knowledge references. |
| Integrity badge shows a warning icon | The recorded hash did not match the MVUU entry. Regenerate the traceability report and telemetry bundle to re-compute hashes. |

## Verification evidence

Automated tests cover the new overlays end-to-end:

- CLI telemetry serialization and signature verification tests live at
  `tests/unit/cli/test_mvuu_dashboard_telemetry.py`.
- Overlay rendering snapshots and signature validation logic are exercised in
  `tests/unit/interface/test_mvuu_dashboard.py`.
- Telemetry builders and signature helpers are validated by
  `tests/unit/interface/test_autoresearch_telemetry.py`.

Refer to `traceability_autoresearch.json` for a signed example bundle after
running the CLI with overlays enabled.

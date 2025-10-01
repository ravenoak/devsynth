# MVUU Traceability Dashboard

The MVUU (Minimum Viable Utility Unit) dashboard renders Streamlit views for
traceability data exported by `devsynth mvu report`. Planned Autoresearch
overlays will surface investigation timelines, provenance filters, and integrity
badges once the external Autoresearch bridge begins delivering signed telemetry.
Until the MCP → A2A → SPARQL connectors ship, all Autoresearch references in this
guide describe preview flows that rely on local fixtures rather than live
telemetry.

## Enabling the dashboard

```bash
poetry run devsynth mvuu-dashboard
```

Running the command without extra flags renders the classic TraceID sidebar and
details pane. The CLI automatically regenerates `traceability.json` before
launching Streamlit.

## Opting into Autoresearch overlays

Autoresearch overlays will remain opt-in because they include extra provenance
data and digital signatures. Enable the stubbed flow when launching the CLI to
exercise the interface ahead of the external rollout. The command below operates
entirely against placeholder payloads until the external bridge is online:

```bash
export DEVSYNTH_AUTORESEARCH_SECRET="<shared hmac secret>"
poetry run devsynth mvuu-dashboard \
  --research-overlays \
  --telemetry-path traceability_autoresearch.json
```

The CLI will emit a signed telemetry bundle containing:

- `timeline`: chronological Autoresearch events with agent persona metadata and
  knowledge-graph references.
- `provenance_filters`: filter definitions the dashboard uses to scope the
  sidebar controls.
- `integrity_badges`: verification summaries for each TraceID, including the
  hash of the MVUU payload used during signing.

While the Autoresearch service remains external, the CLI stores placeholder
signatures alongside the payload in JSON form and logs that no remote telemetry
was contacted. The dashboard reads
`DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY` to determine which environment variable
holds the shared secret (defaults to `DEVSYNTH_AUTORESEARCH_SECRET`). Replace the
placeholder with the production secret once the MCP and A2A connectors go live.

## Privacy and redaction

Autoresearch payloads may include references to knowledge-graph nodes, external
papers, or sensitive transcripts. Before sharing telemetry files:

1. Review the `timeline` entries and redact knowledge references that should not
   leave the organisation.
2. Use dedicated secrets per review environment to avoid leaking signing keys.
3. Rotate secrets when audits are complete so telemetry cannot be reused by
   unauthorised parties.

The CLI writes telemetry with tight defaults—only hashed evidence will leave the
local workstation once the SPARQL gateway is activated. During the preview
period, fixture files mimic the payload so teams can validate workflow updates
without contacting the external service. Additional data must be explicitly
added to the traceability report.

## Troubleshooting overlays

| Symptom | Resolution |
| --- | --- |
| Dashboard shows “telemetry was not found” | Ensure the CLI ran with `--research-overlays` or set `DEVSYNTH_AUTORESEARCH_OVERLAYS=1` after generating telemetry. Preview builds emit a stub file named `traceability_autoresearch.json.stub`. |
| Signature validation failed | Confirm `DEVSYNTH_AUTORESEARCH_SIGNATURE_KEY` points to an environment variable that is set when Streamlit launches. Replace stub secrets once Autoresearch provides production keys. |
| No filters appear in the sidebar | The telemetry `provenance_filters` list was empty. Re-run `devsynth mvuu-dashboard --research-overlays` after confirming the MVUU report contains agent personas and knowledge references or update the stub fixture. |
| Integrity badge shows a warning icon | The recorded hash did not match the MVUU entry. Regenerate the traceability report and telemetry bundle to re-compute hashes, or acknowledge the warning if running against preview fixtures. |

## Verification evidence

Automated tests cover the new overlays end-to-end using fixture payloads until
the external bridge is available:

- CLI telemetry serialization and signature verification tests live at
  `tests/unit/cli/test_mvuu_dashboard_telemetry.py`.
- Overlay rendering snapshots and signature validation logic are exercised in
  `tests/unit/interface/test_mvuu_dashboard.py`.
- Telemetry builders and signature helpers are validated by
  `tests/unit/interface/test_autoresearch_telemetry.py`.

Refer to `traceability_autoresearch.json` for a signed example bundle once the
external Autoresearch service delivers telemetry. Until then, rely on
`traceability_autoresearch.json.stub` to validate configuration.

## Autoresearch Integration Path

The MVUU dashboard depends on the broader Autoresearch sequencing:

1. **MCP tool exposure** enables the CLI to request telemetry generation from
   the external service.
2. **A2A orchestration** ensures WSDE personas can coordinate dashboard updates
   during research sessions.
3. **SPARQL access** unlocks read/write operations for provenance filters and
   badge integrity checks.

Keep overlays behind feature flags until all three layers are operational to
avoid implying local Autoresearch ingestion or telemetry collection.

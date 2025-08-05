# MVUU Dashboard

The MVUU dashboard provides an interactive view of commit traceability data
stored in a local `traceability.json` file (not committed to the repository). It
lists available TraceIDs and shows the linked issue and affected files for each
entry.

![MVUU Dashboard](mvuu_dashboard.svg)

## Usage

To populate the dashboard, DevSynth generates a fresh traceability report:

```bash
$ devsynth mvu report --output traceability.json
```

The `mvuu-dashboard` command runs this step automatically and then launches a
Streamlit application that reads `traceability.json` and displays TraceIDs,
affected files, and related issues:

```bash
$ devsynth mvuu-dashboard
```

If report generation fails, the dashboard falls back to any existing
`traceability.json`.

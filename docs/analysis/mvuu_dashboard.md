# MVUU Dashboard

The MVUU dashboard provides an interactive view of commit traceability data
stored in a local `traceability.json` file (not committed to the repository). It
lists available TraceIDs and shows the linked issue and affected files for each
entry.

![MVUU Dashboard](mvuu_dashboard.svg)

## Usage

Run the dashboard using the DevSynth CLI:

```bash
$ devsynth mvuu-dashboard
```

The command launches a Streamlit application that reads the local
`traceability.json` and displays TraceIDs, affected files, and related issues.

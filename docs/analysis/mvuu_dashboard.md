# MVUU Dashboard

The MVUU dashboard provides an interactive view of commit traceability data
stored in `traceability.json`. It lists available TraceIDs and shows the linked
issue and affected files for each entry.

![MVUU Dashboard](mvuu_dashboard.svg)

## Usage

Run the dashboard using the DevSynth CLI:

```bash
$ devsynth mvuu-dashboard
```

The command launches a Streamlit application that reads `traceability.json` and
displays TraceIDs, affected files, and related issues.

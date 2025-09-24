# Fast + Medium Test Evidence

Store combined fast+medium test artifacts for the 0.1.0a1 release here. Create a
new subdirectory for each evidence drop using the UTC timestamp pattern
`YYYYMMDDTHHMMSSZ-fast-medium/` (for example,
`20250921T164512Z-fast-medium/`).  The timestamp uses ISO-8601 basic format with
UTC indicated by the trailing `Z` and should match the moment the artifacts were
produced.

Inside each timestamped folder:

- Archive coverage output as zipped HTML bundles named
  `htmlcov-<timestamp>-fast-medium.zip` so they can be tracked alongside the raw
  reports.
- Capture the relevant log files (e.g. copies from `logs/` and
  `diagnostics/`) that prove which commands ran and their environment details.
- Include any additional evidence (screenshots, JSON summaries, etc.) necessary
  to reconstruct the release rehearsal.

Leave this directory empty between drops; the adjacent `.gitkeep` ensures the
folder remains in version control when no artifacts are present.

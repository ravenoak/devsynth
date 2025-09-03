Diagnostics artifacts

Purpose
- Store lightweight, human-auditable outputs from validation steps (pytest collection, doctor, marker verification, inventories).

Retention policy
- Keep latest per task/run; prune bulky or superseded blobs. Do not commit large binaries. Prefer .txt/.md summaries.

Commit policy
- Repository ignores diagnostics/* by default, but whitelists .gitkeep, *.txt, *.md, and this README.md to allow curated evidence to be versioned when appropriate.

# GitHub Actions Workflow Policy (post-tag branch)

Workflows once again listen to `push` and `pull_request` events on `main` and `release/*` branches. The primary CI pipeline (`ci.yml`) also runs on a nightly schedule (`cron: '0 6 * * *'`) so the automation posture returns to normal immediately after tagging `v0.1.0a1`.

- Manual `workflow_dispatch` remains available for ad-hoc reruns.
- Until maintainers tag `v0.1.0a1`, keep this branch unmerged to avoid re-enabling automation prematurely.

Refer to `AGENTS.md` and `docs/tasks.md` item 10.1 for the release-specific timing guidance.

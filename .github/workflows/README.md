# GitHub Actions Workflow Policy

All workflows in this directory are configured to run only via [`workflow_dispatch`](https://docs.github.com/actions/using-workflows/events-that-trigger-workflows#workflow_dispatch).

- No `push`, `pull_request`, or scheduled triggers are defined.
- Branch protection ensures direct pushes to `main` are blocked, preventing push-triggered workflows.

To run a workflow, trigger it manually from the GitHub Actions tab.

# Recovering a Stuck PR after a Force-Pushed Rebase (Lossless)

Context
- You rebased release-prep on top of main and force-pushed.
- GitHub now refuses to “Rebase and merge” (or merge at all) into main.

Typical root causes (checklist)
1) Required status checks tied to old commits are missing on the new tip.
   - Re-run CI or wait for checks to finish. Ensure the PR shows green checks for the latest commit.
2) Approvals were dismissed by force-push.
   - Ask reviewers to re-approve. Many orgs auto-dismiss approvals on force-push.
3) Branch protection disallows the chosen merge method.
   - “Rebase and merge” may be disabled on main. If so, use “Squash and merge” or “Create a merge commit,” if allowed.
4) PR is “out of date with base”.
   - Use Update branch (creates a merge commit) or rebase locally again. If policy forbids merge commits, avoid Update branch and use the rescue flows below.
5) Hidden conflicts.
   - GitHub may show no quick-fix button but list file conflicts. Resolve locally.

Lossless resolution strategies
These options preserve all work on release-prep.

Option A — Open a fresh PR from the rebased tip (preferred when the old PR is wedged)
- Why: Clean state; avoids stale checks/approvals entangled with old SHAs.
- Steps:
  1. Ensure release-prep has your intended tip on origin: `git fetch origin && git checkout release-prep && git status`.
  2. Create a clean branch from that tip: `git switch -c release-prep-pr && git push -u origin release-prep-pr`.
  3. Open a new PR: base=main, compare=release-prep-pr. Close the stuck PR with a link to the new one.

Option B — Rescue branch: replay or merge release-prep onto main
- Why: Satisfies branch protections that disallow rebase merges but allow merge commits or clean history.
- Two modes:
  - Cherry-pick (history rewrite to linearize): start from main and replay the unique commits from release-prep.
  - Merge commit (no-ff): bring release-prep in as a single merge commit.
- Scripted helper available: scripts/git_rebase_merge_rescue.sh
  - Examples:
    - Cherry-pick mode: `./scripts/git_rebase_merge_rescue.sh --base main --branch release-prep --mode cherry-pick`
    - Merge mode: `./scripts/git_rebase_merge_rescue.sh --base main --branch release-prep --mode merge`
  - The script creates a branch like `rescue/release-prep-onto-main-YYYYmmdd-HHMMSS` and guides you to push and open a PR.

Option C — Temporarily allow a different merge method
- If branch protection allows admins to toggle merge methods:
  - Temporarily enable “Create a merge commit” or “Squash and merge”.
  - Merge the PR, then restore the original settings. Document the change in the PR for auditability.

Option D — Admin override (last resort)
- If policy permits, admins can override merge protections.
- Before using it:
  - Ensure CI is green and approvals are re-collected if required.
  - Post a comment linking to checks and stating why an override is necessary.

How to use the rescue script (detailed)
1) Ensure a clean working tree: `git status` shows no changes.
2) Run one of the modes:
   - Cherry-pick: linear, best when main must stay without merge commits.
     `./scripts/git_rebase_merge_rescue.sh --mode cherry-pick`
   - Merge: one merge commit, preserves branch identity.
     `./scripts/git_rebase_merge_rescue.sh --mode merge`
3) Resolve conflicts if they occur, then continue (`git cherry-pick --continue` or finish the merge).
4) Push and open a PR:
   `git push -u origin <printed-rescue-branch>`
5) Close or supersede the stuck PR, referencing the new PR.

Preventative practices
- Avoid force-pushing shared PR branches close to merge time; prefer adding a final “sync with main” commit or rebasing earlier in the lifecycle.
- If you must force-push, coordinate with reviewers; expect approvals to be dismissed.
- Ensure required checks run on the new tip; re-run as needed.
- Confirm repository settings: which merge methods are allowed on main? Align your workflow accordingly.

FAQ
- Will I lose commits by cherry-picking? No—content is preserved. Commit SHAs change (new commits), but diffs and authorship remain (with -x footer indicating origin).
- Can I keep a clean linear history? Yes—use the cherry-pick mode in the rescue script.
- Why did GitHub block “Rebase and merge”? It’s disabled if the PR isn’t up-to-date, has conflicts, or the repository disables that method on the base branch.

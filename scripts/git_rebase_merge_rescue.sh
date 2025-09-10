#!/usr/bin/env bash
set -euo pipefail

# git_rebase_merge_rescue.sh
# Purpose: Safely create a rescue branch from base (default: main) and bring in
#          the work from a feature branch (default: release-prep) without losing commits.
# Modes:
#   - cherry-pick: linear history; cherry-pick the unique commits from feature onto base
#   - merge:       create a single no-ff merge commit of feature into base
#
# Usage examples:
#   ./scripts/git_rebase_merge_rescue.sh --mode cherry-pick
#   ./scripts/git_rebase_merge_rescue.sh --mode merge --base main --branch release-prep
#
# Notes:
# - Requires a clean working tree.
# - You will be prompted to resolve conflicts if any.
# - At the end, push the printed branch and open a PR.

BASE_BRANCH="main"
FEATURE_BRANCH="release-prep"
MODE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base)
      BASE_BRANCH="$2"; shift 2 ;;
    --branch)
      FEATURE_BRANCH="$2"; shift 2 ;;
    --mode)
      MODE="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 --mode <cherry-pick|merge> [--base <base-branch>] [--branch <feature-branch>]";
      exit 0 ;;
    *)
      echo "Unknown argument: $1"; exit 2 ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Error: --mode is required (cherry-pick|merge)" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree is not clean. Commit or stash changes before running." >&2
  exit 2
fi

echo "Fetching latest from origin..."
git fetch --prune origin

# Validate branches exist
if ! git show-ref --verify --quiet "refs/remotes/origin/${BASE_BRANCH}"; then
  echo "Error: base branch 'origin/${BASE_BRANCH}' not found." >&2
  exit 2
fi
if ! git show-ref --verify --quiet "refs/remotes/origin/${FEATURE_BRANCH}"; then
  echo "Error: feature branch 'origin/${FEATURE_BRANCH}' not found." >&2
  exit 2
fi

# Ensure local branches are updated
if git show-ref --verify --quiet "refs/heads/${BASE_BRANCH}"; then
  git checkout "$BASE_BRANCH"
  git reset --hard "origin/${BASE_BRANCH}"
else
  git checkout -b "$BASE_BRANCH" "origin/${BASE_BRANCH}"
fi

# Create timestamped rescue branch from base
STAMP=$(date +%Y%m%d-%H%M%S)
RESCUE_BRANCH="rescue/${FEATURE_BRANCH}-onto-${BASE_BRANCH}-${STAMP}"

echo "Creating rescue branch: ${RESCUE_BRANCH} from ${BASE_BRANCH}"
git switch -c "$RESCUE_BRANCH" "$BASE_BRANCH"

if [[ "$MODE" == "cherry-pick" ]]; then
  echo "Determining unique commits on ${FEATURE_BRANCH} not in ${BASE_BRANCH}..."
  MERGE_BASE=$(git merge-base "origin/${BASE_BRANCH}" "origin/${FEATURE_BRANCH}")
  echo "Merge-base is ${MERGE_BASE}"
  echo "Cherry-picking commits from ${MERGE_BASE}..origin/${FEATURE_BRANCH}"
  # Use -x to record original SHA in commit messages
  set +e
  git cherry-pick -x "${MERGE_BASE}..origin/${FEATURE_BRANCH}"
  status=$?
  set -e
  if [[ $status -ne 0 ]]; then
    echo "Cherry-pick stopped due to conflicts. Resolve conflicts, then run:"
    echo "  git add -A && git cherry-pick --continue"
    echo "or abort with:"
    echo "  git cherry-pick --abort && git switch - && git branch -D ${RESCUE_BRANCH}"
    echo "After resolving and finishing cherry-picks, push with:"
    echo "  git push -u origin ${RESCUE_BRANCH}"
    exit $status
  fi
  echo "Cherry-pick completed."
elif [[ "$MODE" == "merge" ]]; then
  echo "Merging origin/${FEATURE_BRANCH} into ${RESCUE_BRANCH} with --no-ff"
  set +e
  git merge --no-ff --no-edit "origin/${FEATURE_BRANCH}"
  status=$?
  set -e
  if [[ $status -ne 0 ]]; then
    echo "Merge has conflicts. Resolve them, then run:"
    echo "  git add -A && git commit"
    echo "To abort the merge and delete the rescue branch:"
    echo "  git merge --abort && git switch - && git branch -D ${RESCUE_BRANCH}"
    exit $status
  fi
  echo "Merge completed."
else
  echo "Error: unknown mode '$MODE' (expected 'cherry-pick' or 'merge')." >&2
  exit 2
fi

echo
echo "Success! Review your changes on ${RESCUE_BRANCH}. When ready, push and open a PR:"
echo "  git push -u origin ${RESCUE_BRANCH}"
echo "Base: ${BASE_BRANCH}  Compare: ${RESCUE_BRANCH}"

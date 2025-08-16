# Issue 131: Resolve pytest-xdist assertion errors
Milestone: 0.1.0-alpha.1

Running `devsynth run-tests` across speed categories triggers internal pytest-xdist assertion errors, preventing full suite completion.

## Plan

- Investigate pytest-xdist configuration and plugin compatibility.
- Ensure `devsynth run-tests` completes without internal assertion errors across fast, medium, and slow categories.

## Status

- Status: open

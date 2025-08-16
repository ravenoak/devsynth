# Resolve pytest-xdist assertion errors
Milestone: 0.1.0-alpha.1
Status: open

Priority: high
Dependencies: None


Running `devsynth run-tests` across speed categories triggers internal pytest-xdist assertion errors, preventing full suite completion.

## Plan

- Investigate pytest-xdist configuration and plugin compatibility.
- Ensure `devsynth run-tests` completes without internal assertion errors across fast, medium, and slow categories.



## Progress

- Attempted `devsynth run-tests --speed=fast`; after initial output the process hung and required manual interruption, indicating ongoing runner issues.

## References

- None

# Security Policy

This policy outlines how we approach security in DevSynth and how contributors can help maintain a secure codebase.

- We run automated security scans for code (Bandit) and dependencies (Safety) in CI for every push and PR. See `docs/security/security_scans.md` for details and local usage.
- Findings are triaged promptly. Prefer fixes over suppressions; document any exception with a justification and time-bounded remediation plan.
- Align with principles in `.junie/the_real_core.md` and development guidance in `project guidelines`.
- Sensitive operations (e.g., provider keys) should use environment variables and never be hard-coded or committed.
- Example and test code must also avoid insecure patterns unless intentionally included for testing—with clear markers and isolation.

## Reporting a Vulnerability

If you discover a vulnerability, please open a private security advisory or contact the maintainers following the repository’s contribution guidelines. Include reproduction steps and potential impact.

## Scope

- Application code under `src/`
- Packaging and scripts under `scripts/`
- CI workflows under `.github/workflows/`

## Baseline and Continuous Improvement

- Initial scans are advisory. Once the baseline is clean and exceptions documented, we will enable stricter CI gates.
- Security work ties into release milestones and the roadmap (see `docs/roadmap/`).

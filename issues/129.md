# Issue 129: Refine environment provisioning to skip heavy GPU packages
Milestone: 0.1.0-alpha.1

Repeated executions of the environment provisioning script attempted to install NVIDIA GPU packages, resulting in endless `Installing nvidia/__init__.py over existing file` messages and a hung process.

## Plan
- Adjust dependency installation to include only required extras.
- Verify the environment provisioning script completes without repeated NVIDIA installation messages.
- Document the expected environment footprint.

## Status
- The environment provisioning script installs the `tests`, `retrieval`, `chromadb`, and `api` extras only.
- Verification complete; the script ran without repeated NVIDIA installation messages ([0b4a60d4](../commit/0b4a60d4)).
- Status: closed

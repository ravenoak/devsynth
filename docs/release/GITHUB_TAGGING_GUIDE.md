# DevSynth v0.1.0a1 GitHub Tagging Guide

## Prerequisites
✅ **All remediation tasks completed** - See `docs/release/0.1.0-alpha.1.md` for current status
✅ **UAT bundle created** - Located at `artifacts/releases/0.1.0a1/uat-bundle-$(date -u +%Y%m%dT%H%M%SZ)/`
✅ **Release artifacts ready** - Wheel and sdist built in `dist/`
✅ **Evidence documented** - Dialectical audit log updated with remediation summary

## Step-by-Step Tagging Process

### 1. Verify Current Status
```bash
# Ensure you're on the main branch
git checkout main
git status  # Should show clean working directory

# Verify latest commit
git log --oneline -5
```

### 2. Create GitHub Release Draft
1. Go to [GitHub Releases](https://github.com/ravenoak/devsynth/releases)
2. Click "Create a new release"
3. **Tag version**: `v0.1.0a1`
4. **Target**: `main` branch
5. **Title**: `DevSynth v0.1.0a1 (Alpha Release)`
6. **Description**: Copy from `docs/release/0.1.0-alpha.1.md` section "Release Notes Summary"

### 3. Upload Release Assets
Attach the following files to the GitHub release:
- `dist/devsynth-0.1.0a1-py3-none-any.whl`
- `dist/devsynth-0.1.0a1.tar.gz`
- `artifacts/releases/0.1.0a1/final/INDEX.md` (if created)

### 4. Publish the Release
- ✅ **Pre-release**: Check this box (it's an alpha release)
- Click **"Publish release"**

### 5. Post-Release Actions

#### Enable GitHub Actions Workflows
After the tag is published, create a PR to re-enable CI triggers:

1. **Create PR from draft**: Use `artifacts/pr_drafts/re-enable-workflows-post-v0-1-0a1.patch`
2. **Review changes**: Ensure only `workflow_dispatch` triggers are replaced with push/pull_request/schedule
3. **Merge PR**: This will enable automated CI for future commits

#### Update Version for Development
```bash
# Update version to next development version (e.g., 0.1.0a2.dev0)
# This should be done in a separate PR after tagging
```

#### Archive Final Evidence
```bash
# Copy UAT bundle to final archive location
cp -r artifacts/releases/0.1.0a1/uat-bundle-* artifacts/releases/0.1.0a1/final/
```

## Evidence Artifacts for Release

The following evidence supports this v0.1.0a1 release:

### Test Infrastructure
- **Test Collection**: 5,739+ tests collecting successfully
- **Coverage**: 24.62% baseline (infrastructure working)
- **MyPy Strict**: 0 errors across 434 source files
- **Smoke Tests**: Passing with proper plugin loading

### Release Automation
- **task release:prep**: ✅ Complete success
- **Wheel/SDist**: ✅ Built and installable
- **Fresh venv install**: ✅ Working (Python 3.12+ compatibility)

### Documentation
- **Release Notes**: Updated with current evidence
- **UAT Bundle**: Complete evidence package
- **Dialectical Audit**: Updated with remediation summary

## Troubleshooting

### If Tagging Fails
- Ensure you're a repository maintainer
- Verify tag doesn't already exist: `git tag -l | grep v0.1.0a1`
- Check GitHub permissions for releases

### If CI Fails After Tag
- The workflows are currently `workflow_dispatch` only
- Use the post-tag PR to restore automated triggers
- Manual dispatch URLs documented in release notes

### If Package Installation Issues
- Verify Python version compatibility (>=3.12, <3.15)
- Check wheel integrity: `unzip -l dist/devsynth-0.1.0a1-py3-none-any.whl`
- Test in clean environment: `python -m venv /tmp/test && pip install dist/devsynth-0.1.0a1-py3-none-any.whl`

## Support
For questions about the release process, refer to:
- `docs/release/0.1.0-alpha.1.md` - Current status and evidence
- `issues/release-finalization-uat.md` - UAT session details
- `docs/policies/dialectical_audit.md` - Audit policy reference

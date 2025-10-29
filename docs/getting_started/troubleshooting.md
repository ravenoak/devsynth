---

title: "DevSynth Troubleshooting Guide"
date: "2025-06-01"
version: "0.1.0a1"
tags:
  - "troubleshooting"
  - "getting-started"
  - "common-issues"
  - "solutions"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-08-24"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Getting Started</a> &gt; DevSynth Troubleshooting Guide
</div>

# DevSynth Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using DevSynth. If you're experiencing problems, check this guide before submitting an issue.

## Environment Requirements

Ensure your environment is running **Python 3.12 or higher**. Managing dependencies with Poetry can help avoid version conflicts.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Configuration Issues](#configuration-issues)
- [Provider Issues](#llm-provider-issues)
- [Memory System Issues](#memory-system-issues)
- [Command Execution Issues](#command-execution-issues)
- [Performance Issues](#performance-issues)
- [Getting Additional Help](#getting-additional-help)

## Installation Issues

### Python Version Compatibility

**Issue**: Installation fails with Python version errors.

**Solution**:
- Ensure you have Python 3.12 or higher installed
- Check your Python version with `python --version`
- Consider using a tool like pyenv to manage multiple Python versions

### Poetry Installation Problems

**Issue**: Problems with Poetry installation or dependency resolution.

**Solution**:
- Ensure you have the latest version of Poetry installed
- Try running `poetry update` to update dependencies
- Clear Poetry's cache with `poetry cache clear --all .`
- Check for conflicting dependencies in your project

## Configuration Issues

### Missing API Keys

**Issue**: DevSynth reports missing API keys.

**Solution**:
- Ensure you have set up the required API keys in your environment or .env file
- For OpenAI integration: Set the `OPENAI_API_KEY` environment variable
- For Serper integration: Set the `SERPER_API_KEY` environment variable
- Check that your .env file is in the correct location (project root)

### Configuration File Issues

**Issue**: DevSynth can't find or load configuration files.

**Solution**:
- Verify that the configuration file exists in the expected location
- Check file permissions to ensure DevSynth can read the file
- Validate the configuration file format (should be valid YAML)
- Try running `devsynth config --reset` to reset to default configuration

### Running `devsynth doctor`

Use this command to check your environment and configuration files. It warns
about Python versions below 3.12 and any missing API keys.

```bash
$ devsynth doctor
No project configuration found. Run 'devsynth init' to create it.
Warning: Python 3.12 or higher is required. Current version: 3.10.0
Missing environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY
Configuration issues detected. Run 'devsynth init' to generate defaults.

$ devsynth doctor
All configuration files are valid.
```

## Provider Issues

### Default provider behavior (offline-safe)

By default, DevSynth does not require any remote LLM provider. A lightweight built-in provider is used for smoke paths and CLI help flows so that commands do not hang when credentials are absent or network is unavailable. If you explicitly select a remote provider (e.g., `DEVSYNTH_PROVIDER=openai`) without credentials, startup will fail fast with a clear error instead of silently falling back.

### Connection Errors with LM Studio

**Issue**: DevSynth can't connect to LM Studio.

**Solution**:
- Ensure LM Studio is running on your machine
- Verify the endpoint configuration (default: http://localhost:1234/v1)
- Check network connectivity and firewall settings
- Try restarting LM Studio

### OpenAI API Issues

**Issue**: Problems connecting to OpenAI API.

**Solution**:
- Verify your API key is valid and has sufficient credits
- Check your internet connection
- Ensure you're not hitting rate limits
- Try using a different model or reducing request frequency

### Model Loading Errors

**Issue**: Errors when loading or using specific models.

**Solution**:
- Verify the model name is correct
- Ensure the model is available in your LM Studio installation
- Check if you have sufficient system resources (RAM, disk space)
- Try using a smaller model if you're experiencing memory issues

## Memory System Issues

### Optional Extras Installation Issues

These extras are optional and commonly used in development/testing. Installation may fail due to platform wheels, compiler toolchains, or Python/C++ ABI constraints. Prefer Poetry for consistency; pip commands are provided for PyPI installs.

#### FAISS (faiss-cpu)

Issue:
- Installation fails with errors about missing BLAS/LAPACK, MKL, or incompatible wheels.

Solutions:
- Poetry (recommended):
  - macOS (Apple Silicon / Intel): poetry add faiss-cpu -E retrieval
  - Linux (x86_64): poetry add faiss-cpu -E retrieval
  - Windows: faiss prebuilt wheels are limited; use WSL2 Ubuntu for best support.
- pip alternative:
  - pip install faiss-cpu
- Notes:
  - Ensure Python version is 3.12+ to match this project.
  - Avoid faiss-gpu unless you’ve configured CUDA; prefer faiss-cpu for CI/dev.
  - If installation continues to fail, set DEVSYNTH_RESOURCE_FAISS_AVAILABLE=false to skip FAISS-dependent tests.

#### Kuzu

Issue:
- Build errors or wheel not found for your platform.

Solutions:
- Poetry (recommended): poetry add kuzu -E retrieval
- pip alternative: pip install kuzu
- Platform hints:
  - Linux/macOS: Recent Python versions usually have binary wheels; older platforms may build from source and require a C++ toolchain.
  - Windows: Prefer WSL2; native builds may require MSVC Build Tools.
- If not needed, skip Kuzu-dependent tests by setting DEVSYNTH_RESOURCE_KUZU_AVAILABLE=false.

#### ChromaDB (+ tiktoken)

Issue:
- Install fails on tiktoken or pydantic-related wheels; or runtime import errors for chromadb.

Solutions:
- Poetry (recommended): poetry add chromadb tiktoken -E chromadb
- pip alternative: pip install "chromadb>=0.5" tiktoken
- Platform hints:
  - Ensure Rust toolchain if tiktoken attempts a local build: curl https://sh.rustup.rs -sSf | sh
  - macOS: xcode-select --install to install command line tools.
  - Linux: Ensure python3-dev headers and a C++ compiler (e.g., build-essential on Debian/Ubuntu).
- To bypass when optional: set DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=false.

#### LMDB / DuckDB / TinyDB

Issue:
- Optional memory backends fail to install or import.

Solutions:
- Poetry:
  - poetry add lmdb duckdb tinydb -E memory
- pip:
  - pip install lmdb duckdb tinydb
- Skip when unavailable using flags:
  - DEVSYNTH_RESOURCE_LMDB_AVAILABLE=false
  - DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=false
- TinyDB is pure-Python and typically trouble-free.

### ChromaDB Issues

**Issue**: Problems with the ChromaDB memory store.

**Solution**:
- Ensure ChromaDB is properly installed
- Check the memory file path configuration
- Verify file permissions for the ChromaDB directory
- Try clearing the ChromaDB cache

### Memory Persistence Problems

**Issue**: Memory items not persisting between sessions.

**Solution**:
- Ensure you're using a persistent memory store type (file or ChromaDB)
- Check the memory file path configuration
- Verify file permissions for the memory directory
- Make sure you're properly saving items before ending the session

## Command Execution Issues

### Smoke tests hang or never complete

Issue: Long-running or hanging behavior during basic test runs.

Solutions:
- Use the fast smoke profile without xdist and with minimal plugins. For example: `poetry run pytest -m fast -q`.
- Prefer the helper: `./scripts/run_all_tests.py --unit` for a quick check without optional integrations.
- Ensure you are not forcing a remote provider without credentials. Unset `DEVSYNTH_PROVIDER` or set it to a local/offline mode.
- Avoid loading heavy pytest plugins implicitly in minimal environments. If you used scripts that set `PYTEST_DISABLE_PLUGIN_AUTOLOAD`, make sure to unset it when running the broader suite.

### Command Not Found

### Command Not Found

**Issue**: DevSynth commands not recognized.

**Solution**:
- Ensure DevSynth is properly installed
- Check that the DevSynth executable is in your PATH
- Try reinstalling DevSynth
- If using a virtual environment, ensure it's activated

### Command Execution Failures

**Issue**: Commands fail to execute or complete.

**Solution**:
- Check the error message for specific issues
- Ensure all required files exist and are accessible
- Verify you have sufficient permissions
- Check for syntax errors in your input files

## Performance Issues

### Slow Response Times

**Issue**: DevSynth operations are taking too long.

**Solution**:
- Consider using a more powerful LLM model
- Optimize your input prompts to be more concise
- Reduce the complexity of your requirements
- Check system resource usage during operation

### High Memory Usage

**Issue**: DevSynth is using excessive memory.

**Solution**:
- Configure a smaller context size
- Use a more memory-efficient LLM model
- Close other memory-intensive applications
- Consider upgrading your system's RAM

## Getting Additional Help

If you're experiencing issues not covered in this guide:

1. Check the [User Guide](../user_guides/user_guide.md) for more detailed information
2. Review the [GitHub Issues](https://github.com/ravenoak/devsynth/issues) for similar problems
3. Join the DevSynth community for support
4. Submit a detailed bug report with steps to reproduce the issue

When reporting issues, please include:
- DevSynth version
- Python version
- Operating system
- Complete error message
- Steps to reproduce the issue
- Any relevant configuration settings

## Related Documents

- [Installation Guide](installation.md) - Detailed installation instructions
- [Basic Usage Guide](basic_usage.md) - Introduction to basic DevSynth usage
- [User Guide](../user_guides/user_guide.md) - Comprehensive guide for users
- [Configuration Guide](../user_guides/configuration.md) - Guide to configuring DevSynth
## Implementation Status

.

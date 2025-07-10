---
title: "DevSynth Troubleshooting Guide"
date: "2025-06-01"
version: "0.1.0"
tags:
  - "troubleshooting"
  - "getting-started"
  - "common-issues"
  - "solutions"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---

# DevSynth Troubleshooting Guide

This guide provides solutions to common issues you might encounter when using DevSynth. If you're experiencing problems, check this guide before submitting an issue.

## Environment Requirements

Ensure your environment is running **Python 3.11 or higher**. Managing dependencies with Poetry can help avoid version conflicts.

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
- Ensure you have Python 3.11 or higher installed
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
about Python versions below 3.11 and any missing API keys.

```bash
$ devsynth doctor
No project configuration found. Run 'devsynth init' to create it.
Warning: Python 3.11 or higher is required. Current version: 3.10.0
Missing environment variables: OPENAI_API_KEY, ANTHROPIC_API_KEY
Configuration issues detected. Run 'devsynth init' to generate defaults.

$ devsynth doctor
All configuration files are valid.
```

## Provider Issues

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

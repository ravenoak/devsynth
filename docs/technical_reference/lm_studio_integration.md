---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
- technical-reference
title: LM Studio Integration
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; LM Studio Integration
</div>

# LM Studio Integration

This document describes the integration between DevSynth and LM Studio, including how to configure and use LM Studio models with DevSynth.

## Overview

DevSynth can use LM Studio as a provider for language models. LM Studio is a desktop application that allows you to run language models locally on your machine. By integrating with LM Studio, DevSynth can leverage these local models for various tasks, such as requirement analysis, specification generation, test generation, and code generation.

The LM Studio integration is optional. If the `lmstudio` Python package is not installed, these features are disabled and tests that depend on LM Studio are skipped.

**Implementation Status:** The LM Studio provider is stable for local use. Remote model support and advanced streaming remain experimental.

## Prerequisites

- LM Studio installed and running on your machine
- At least one model loaded in LM Studio
- LM Studio API server running (typically at http://localhost:1234)

## Configuration

DevSynth provides several configuration options for the LM Studio integration:

| Setting | Environment Variable | Description | Default Value |
|---------|---------------------|-------------|---------------|
| Provider | DEVSYNTH_LLM_PROVIDER | The Provider to use | "lmstudio" |
| API Base | DEVSYNTH_LLM_API_BASE | Base URL for the LM Studio API | "http://localhost:1234/v1" |
| Model | DEVSYNTH_LLM_MODEL | Model name to use (empty for auto-selection) | "" |
| Max Tokens | DEVSYNTH_LLM_MAX_TOKENS | Maximum tokens for responses | 1024 |
| Temperature | DEVSYNTH_LLM_TEMPERATURE | Temperature for generation | 0.7 |
| Auto-select Model | DEVSYNTH_LLM_AUTO_SELECT_MODEL | Whether to auto-select a model | true |

You can set these options using environment variables or the `config` command:

```bash

# Set using environment variables

export DEVSYNTH_LLM_PROVIDER=lmstudio
export DEVSYNTH_LLM_API_BASE=http://localhost:1234/v1
export DEVSYNTH_LLM_MODEL=my_model
export DEVSYNTH_LLM_MAX_TOKENS=2048
export DEVSYNTH_LLM_TEMPERATURE=0.8
export DEVSYNTH_LLM_AUTO_SELECT_MODEL=true

# Set using config command

devsynth config --key llm_provider --value lmstudio
devsynth config --key llm_api_base --value http://localhost:1234/v1
devsynth config --key llm_model --value my_model
devsynth config --key llm_max_tokens --value 2048
devsynth config --key llm_temperature --value 0.8
devsynth config --key llm_auto_select_model --value true
```

## Listing Available Models

You can list the available models from LM Studio using the `config` command with the `--list-models` option:

```bash
devsynth config --list-models
```

This will display a table of available models with their IDs, names, and owners.

## Selecting a Model

You can select a model in two ways:

1. Using the `config` command with the `--key` option:

```bash
devsynth config --key llm_model
```

This will list the available models and prompt you to select one.

2. Using the `config` command with both `--key` and `--value` options:

```bash
devsynth config --key llm_model --value my_model
```

This will set the model directly without prompting.

If you don't specify a model, DevSynth will auto-select the first available model from LM Studio.

## Auto-selection

By default, DevSynth will auto-select the first available model from LM Studio if no model is specified. You can disable this behavior by setting the `llm_auto_select_model` option to `false`:

```bash
devsynth config --key llm_auto_select_model --value false
```

## Error Handling

DevSynth includes robust error handling for the LM Studio integration:

- If LM Studio is not available, DevSynth will fall back to a default model name ("local_model") and log a warning.
- If the specified model is not available, DevSynth will raise an error and suggest listing available models.
- If there's an issue with the LM Studio API, DevSynth will provide detailed error messages to help diagnose the problem.

## Testing the Integration

You can test the LM Studio integration using the provided test script:

```bash
python /tmp/test_lmstudio.py
```

This script tests various aspects of the integration, including listing models, generating text, and generating text with context.

## Troubleshooting

If you encounter issues with the LM Studio integration, try the following:

1. Ensure LM Studio is running and the API server is enabled (typically at http://localhost:1234).
2. Check that at least one model is loaded in LM Studio.
3. Verify the API base URL is correct (default: http://localhost:1234/v1).
4. Try listing available models to ensure DevSynth can connect to LM Studio.
5. Check the logs for detailed error messages.

## Implementation Details

The LM Studio integration is implemented in the following files:

- `src/devsynth/application/llm/lmstudio_provider.py`: The main provider implementation
- `src/devsynth/config/settings.py`: Configuration settings for LLM providers
- `src/devsynth/application/cli/commands.py`: CLI commands for configuring LLM providers
- `tests/integration/test_lmstudio_provider.py`: Integration tests for the LM Studio provider

The provider uses the official `lmstudio` Python SDK for all API interactions.
`lmstudio.sync_api` is configured with the API host from settings and then used
to create chat completions and embeddings without relying on raw HTTP requests.

The implementation includes the following features:

- Auto-selection of models from LM Studio
- Configuration options for API base, model, max tokens, temperature, etc.
- Robust error handling for connection issues and invalid responses
- Integration tests for verifying functionality
- CLI commands for listing and selecting models

## Current Limitations

- Only local LM Studio servers are supported; remote deployments require manual configuration.
- Streaming responses and advanced model parameters are experimental.

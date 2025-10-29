---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: LLM Integration in DevSynth
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; LLM Integration in DevSynth
</div>

# LLM Integration in DevSynth

This document describes the LLM integration in DevSynth, focusing on the LM Studio provider and token optimization mechanisms.

## Overview

DevSynth supports multiple LLM providers through a flexible adapter pattern.

**Implementation Status:** OpenAI, Anthropic, LM Studio and Offline providers are implemented. When `offline_mode` is enabled the Offline provider is automatically selected.

The current implementation includes the following providers and configuration keys:

- **OpenAI provider** – requires `OPENAI_API_KEY`; accepts `model`, `api_base`, `temperature` and `max_tokens`. Requires internet access.
- **Anthropic provider** – requires `ANTHROPIC_API_KEY` (or `api_key` in configuration) with optional `model`, `api_base`, `temperature`, `max_tokens` and `timeout`.
- **LM Studio provider** – configured via `api_base`, `model`, `max_tokens`, `temperature` and `auto_select_model`. A local LM Studio server must be running.
- **Offline provider** – uses `offline_provider.model_path` to load a local model. If unset it falls back to deterministic text generation for testing.


The LLM integration also includes token tracking and optimization mechanisms to efficiently manage context windows and prevent token limit errors.

## Architecture

The LLM integration follows a layered architecture:

1. **Domain Layer**: Defines the interfaces for LLM providers and factories
2. **Application Layer**: Implements the core Provider classes and token utilities
3. **Adapter Layer**: Provides the adapter for connecting the application to LLM backends


## LM Studio Provider

The LM Studio provider allows DevSynth to connect to a local LM Studio server running on the user's machine. LM Studio is a desktop application that allows users to run LLMs locally.

### Configuration

The LM Studio provider can be configured with the following parameters:

- `api_base`: Base URL for the LM Studio API (default: http://localhost:1234/v1)
- `model`: Model name to use (default: local_model)
- `max_tokens`: Maximum tokens for responses (default: 1024)


### Usage

```python
from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter, LLMProviderConfig

# Create the LLM adapter

adapter = LLMBackendAdapter()

# Create an LM Studio provider

config = LLMProviderConfig(
    provider_type="lmstudio",
    parameters={
        "api_base": "http://localhost:1234/v1",
        "model": "local_model",
        "max_tokens": 1024,
    },
)
provider = adapter.create_provider(config)

# Generate text

response = provider.generate("Hello, world!")

# Generate text with context

context = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
]
response = provider.generate_with_context("Tell me a joke", context)
```

## Offline Provider

When `offline_mode` is enabled in the project configuration, DevSynth selects
the **OfflineProvider**. This provider avoids all remote API calls and either
loads a local Hugging Face model specified via
`offline_provider.model_path` or falls back to deterministic text generation and
hash-based embeddings. Offline mode ensures repeatable results for testing and
continuous integration. See the configuration guide for details on the relevant
flags.

## Token Tracking and Optimization

DevSynth includes a `TokenTracker` utility for tracking and optimizing token usage in LLM interactions.

### Features

- Token counting for text, messages, and conversations
- Context pruning to fit within token limits
- Token limit enforcement
- Fallback tokenizer when tiktoken is not available


### Usage

```python
from devsynth.application.utils.token_tracker import TokenTracker

# Create a token tracker

tracker = TokenTracker()

# Count tokens in text

text = "Hello, world!"
token_count = tracker.count_tokens(text)

# Count tokens in a message

message = {"role": "user", "content": "Hello, world!"}
token_count = tracker.count_message_tokens(message)

# Count tokens in a conversation

conversation = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hello! How can I help you today?"}
]
token_count = tracker.count_conversation_tokens(conversation)

# Prune a conversation to fit within a token limit

max_tokens = 100
pruned_conversation = tracker.prune_conversation(conversation, max_tokens)

# Ensure a text is within a token limit

try:
    tracker.ensure_token_limit(text, max_tokens=50)
except TokenLimitExceededError:
    print("Text exceeds token limit")
```

## Setting Up LM Studio

To use the LM Studio provider:

1. Download and install LM Studio from [https://lmstudio.ai/](https://lmstudio.ai/)
2. Download a model in LM Studio
3. Start a local server with your chosen model
4. Configure the DevSynth LM Studio provider with the correct API base URL and model name


## Implementation Details

### Token Counting

Token counting is implemented using the tiktoken library when available, with a fallback to a simple word-based approximation when tiktoken is not available.

### Context Pruning

The context pruning strategy keeps the system message (if present) and removes older messages until the conversation fits within the token limit. This ensures that the most recent context is preserved while staying within the model's token limits.

### Error Handling

The LM Studio provider includes error handling for API calls, with clear error messages when the API returns an error. The token tracker also includes error handling for token limit enforcement.

## Current Limitations

The core providers are functional, but streaming responses and automatic
provider selection are still experimental. Token counting may miss edge cases
with uncommon tokenizers.

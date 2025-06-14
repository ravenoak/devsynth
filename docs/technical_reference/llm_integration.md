# LLM Integration in DevSynth

This document describes the LLM integration in DevSynth, focusing on the LM Studio provider and token optimization mechanisms.

## Overview

DevSynth supports multiple LLM providers through a flexible adapter pattern.

**Implementation Status:** LM Studio and OpenAI providers are fully implemented. The Anthropic provider remains a stub.

The current implementation includes:

- OpenAI provider (implemented)
- Anthropic provider (stub)
- LM Studio provider (fully implemented)

The LLM integration also includes token tracking and optimization mechanisms to efficiently manage context windows and prevent token limit errors.

## Architecture

The LLM integration follows a layered architecture:

1. **Domain Layer**: Defines the interfaces for LLM providers and factories
2. **Application Layer**: Implements the core LLM provider classes and token utilities
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
from devsynth.adapters.llm.llm_adapter import LLMBackendAdapter

# Create the LLM adapter
adapter = LLMBackendAdapter()

# Create an LM Studio provider
config = {
    "api_base": "http://localhost:1234/v1",
    "model": "local_model",
    "max_tokens": 1024
}
provider = adapter.create_provider("lmstudio", config)

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

Only the LM Studio provider is production ready. The OpenAI and Anthropic
providers are stubs and may not support all features. Integration with other
providers and streaming responses remains experimental. Token counting may miss
edge cases with uncommon tokenizers.

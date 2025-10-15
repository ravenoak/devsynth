---
title: "OpenRouter Provider Specification"
date: "2025-07-14"
version: "0.1.0-alpha.1"
tags:
  - "specifications"
  - "llm"
  - "providers"
  - "openrouter"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-14"
---

<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Specifications</a> &gt; OpenRouter Provider Specification
</div>

# OpenRouter Provider Specification

This document specifies the integration of OpenRouter as an LLM provider in DevSynth, providing access to 400+ AI models through a unified API with support for free-tier models.

## Overview

OpenRouter is a unified API that provides access to multiple AI models from various providers through a single endpoint. This integration enables DevSynth users to:

- Access a wide variety of models (400+ available)
- Use free-tier models for cost-effective development and testing
- Leverage OpenAI-compatible API format for seamless integration
- Benefit from automatic fallback and model routing

## API Integration Details

### Base Configuration

**API Endpoint**: `https://openrouter.ai/api/v1`

**Authentication**: Bearer token authentication via `Authorization: Bearer <OPENROUTER_API_KEY>` header

**Request Format**: OpenAI-compatible JSON format for chat completions and embeddings

### Supported Models

#### Free-Tier Models (Primary Testing Targets)

| Model | Provider | Context Window | Free Tier | Use Case |
|-------|----------|---------------|-----------|----------|
| `google/gemini-flash-1.5` | Google | 1M tokens | ✅ | Fast, cost-effective general tasks |
| `meta-llama/llama-3.1-8b-instruct` | Meta | 128K tokens | ✅ | Open source, good quality |
| `mistralai/mistral-7b-instruct` | Mistral AI | 32K tokens | ✅ | Efficient, good performance |
| `microsoft/wizardlm-2-8x22b` | Microsoft | 64K tokens | ✅ | Long context, high quality |
| `anthropic/claude-3-haiku` | Anthropic | 200K tokens | ✅ | Fast, cost-effective Anthropic model |

#### Premium Models (Optional)

| Model | Provider | Context Window | Use Case |
|-------|----------|---------------|----------|
| `openai/gpt-4` | OpenAI | 128K tokens | High-quality reasoning |
| `anthropic/claude-3-opus` | Anthropic | 200K tokens | Top-tier performance |
| `google/gemini-pro` | Google | 32K tokens | Multimodal capabilities |

### Request/Response Format

#### Chat Completions

**Request**:
```json
{
  "model": "google/gemini-flash-1.5",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**Response**:
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "google/gemini-flash-1.5",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! I'm doing well, thank you for asking."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 12,
    "total_tokens": 22
  }
}
```

#### Embeddings

**Request**:
```json
{
  "model": "text-embedding-ada-002",
  "input": "The quick brown fox jumps over the lazy dog"
}
```

**Response**:
```json
{
  "object": "list",
  "data": [{
    "object": "embedding",
    "embedding": [0.0023, -0.0012, ...],
    "index": 0
  }],
  "model": "text-embedding-ada-002",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

#### Streaming

**Request** (with `stream: true`):
```json
{
  "model": "google/gemini-flash-1.5",
  "messages": [{"role": "user", "content": "Tell me a story"}],
  "stream": true
}
```

**Response Stream**:
```json
data: {"id": "chatcmpl-abc123", "object": "chat.completion.chunk", "created": 1677652288, "model": "google/gemini-flash-1.5", "choices": [{"index": 0, "delta": {"content": "Once"}, "finish_reason": null}]}

data: {"id": "chatcmpl-abc123", "object": "chat.completion.chunk", "created": 1677652288, "model": "google/gemini-flash-1.5", "choices": [{"index": 0, "delta": {"content": " upon"}, "finish_reason": null}]}

data: [DONE]
```

## Provider Implementation

### Class Structure

```python
class OpenRouterProvider(StreamingLLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.model = config.get("model")  # User-selectable
        self.temperature = config.get("temperature", 0.7)
        self.max_tokens = config.get("max_tokens", 4096)
        self.timeout = config.get("timeout", 60)

    def generate(self, prompt: str, parameters: dict = None) -> str:
        """Generate text from a prompt."""

    def generate_with_context(self, prompt: str, context: list[dict], parameters: dict = None) -> str:
        """Generate text with conversation context."""

    def get_embedding(self, text: str) -> list[float]:
        """Get embedding vector for text."""

    async def generate_stream(self, prompt: str, parameters: dict = None) -> AsyncGenerator[str, None]:
        """Generate text with streaming."""

    async def generate_with_context_stream(self, prompt: str, context: list[dict], parameters: dict = None) -> AsyncGenerator[str, None]:
        """Generate text with streaming and context."""
```

### Configuration Schema

#### Application Layer Configuration

```python
@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter provider."""

    # Authentication
    api_key: str | None = None  # OPENROUTER_API_KEY

    # Model settings
    model: str | None = None  # User-selectable, defaults to free tier
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 60

    # Network settings
    base_url: str = "https://openrouter.ai/api/v1"
    max_retries: int = 3
    call_timeout: float = 10.0

    # Resilience settings
    failure_threshold: int = 3
    recovery_timeout: float = 60.0

    # OpenRouter-specific settings
    http_referer: str | None = None  # For app attribution
    x_title: str | None = None       # For app attribution
```

#### Configuration File Schema

```yaml
# config/default.yml
llm:
  providers:
    openrouter:
      enabled: false  # Disabled by default
      api_key: "${OPENROUTER_API_KEY}"
      model: null  # User-selectable, defaults to free tier
      temperature: 0.7
      max_tokens: 4096
      timeout: 60
      base_url: "https://openrouter.ai/api/v1"
      max_retries: 3
      failure_threshold: 3
      recovery_timeout: 60.0
      call_timeout: 10.0
```

### Error Handling

#### Exception Hierarchy

```python
class OpenRouterError(LLMProviderError):
    """Base exception for OpenRouter operations."""

class OpenRouterConnectionError(OpenRouterError, LLMConnectionError):
    """Connection or network error."""

class OpenRouterAuthenticationError(OpenRouterError, LLMAuthenticationError):
    """Authentication failure."""

class OpenRouterModelError(OpenRouterError, LLMModelError):
    """Model or generation error."""

class OpenRouterRateLimitError(OpenRouterError):
    """Rate limit exceeded."""

class OpenRouterInvalidModelError(OpenRouterError):
    """Invalid model specified."""
```

#### Error Response Handling

OpenRouter returns standard HTTP status codes with detailed error messages:

```json
{
  "error": {
    "message": "Invalid API key provided",
    "type": "authentication_error",
    "code": 401
  }
}
```

### Resilience Patterns

#### Retry Logic

- **Exponential backoff**: 1s → 2s → 4s → 8s → 16s (max 60s)
- **Jitter**: Random delay variation to prevent thundering herd
- **Retry conditions**:
  - Network timeouts (5xx errors)
  - Rate limits (429 errors)
  - Temporary server errors (502, 503, 504)

#### Circuit Breaker

- **Failure threshold**: 5 consecutive failures
- **Recovery timeout**: 60 seconds
- **Half-open state**: Allow single request to test recovery

#### Rate Limiting

- **Free tier**: Model-specific rate limits (varies by model)
- **Paid tier**: Higher rate limits based on usage
- **Backoff strategy**: Exponential backoff on 429 responses

### Token Tracking Integration

#### Token Counting

OpenRouter provides token usage in responses:
```json
{
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

#### Context Window Management

- **Model-specific limits**: Check model capabilities before requests
- **Token pruning**: Remove oldest messages when approaching limits
- **Warning thresholds**: Alert when approaching context limits

### Special Headers for Attribution

OpenRouter requires attribution headers for proper API usage:

```python
headers = {
    "Authorization": f"Bearer {self.api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": self.http_referer or "https://devsynth.dev",
    "X-Title": self.x_title or "DevSynth AI Platform"
}
```

## Integration Points

### Provider Factory Integration

```python
# src/devsynth/application/llm/provider_factory.py
_order = ("offline", "local", "openai", "anthropic", "lmstudio", "openrouter")

def create_provider(self, provider_type: str, config: dict = None):
    if provider_type == "openrouter":
        return OpenRouterProvider(config)
```

### Configuration Loading

```python
# src/devsynth/config/settings.py
@dataclass
class LLMSettings:
    openrouter_api_key: str | None = None
    openrouter_model: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
```

### Environment Variables

```bash
# Required
export OPENROUTER_API_KEY="your-api-key-here"

# Optional
export OPENROUTER_MODEL="google/gemini-flash-1.5"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OPENROUTER_HTTP_REFERER="https://your-app.com"
export OPENROUTER_X_TITLE="Your App Name"
```

## Testing Strategy

### Unit Tests

- **Mock all HTTP calls** using `responses` library
- **Test configuration variations** (with/without API key, different models)
- **Test error conditions** (authentication, rate limits, invalid models)
- **Test resilience patterns** (retry logic, circuit breaker activation)
- **Test token tracking** integration

### Integration Tests

- **Test with real OpenRouter API** using resource markers
- **Test multiple free-tier models** (Gemini Flash, Llama 3.1 8B, Mistral 7B)
- **Test rate limiting behavior** with real API responses
- **Test model switching** between different providers
- **Performance benchmarks** for latency and throughput

### BDD Tests

- **Cross-provider scenarios** testing identical behavior
- **Free-tier model validation** scenarios
- **Error handling scenarios** across providers
- **Fallback behavior** when OpenRouter unavailable

## Security Considerations

### API Key Management

- **Environment variables only** - no API keys in configuration files
- **Secure storage** - use system credential stores when available
- **Rotation support** - allow easy key updates
- **Logging sanitization** - never log API keys in error messages

### TLS Enforcement

- **HTTPS only** for all API communications
- **Certificate validation** enabled by default
- **Custom CA support** for enterprise deployments

### Input Validation

- **Model name validation** against known models list
- **Parameter range validation** (temperature 0-2, max_tokens > 0)
- **Request size limits** to prevent abuse

## Performance Characteristics

### Latency Expectations

- **Free-tier models**: 500ms - 2s average response time
- **Premium models**: 1s - 5s average response time
- **Streaming**: Initial chunk within 1s, subsequent chunks every 100-500ms

### Rate Limits

- **Free tier**: Model-specific limits (typically 10-100 requests/minute)
- **Paid tier**: Higher limits based on usage tier
- **Burst handling**: Circuit breaker activation on sustained rate limit hits

### Cost Optimization

- **Default to free models** when no model specified
- **Token-aware routing** to minimize costs
- **Usage tracking** for cost monitoring and optimization

## Migration Guide

### For Existing Users

1. **No breaking changes** - existing configurations continue working
2. **Opt-in integration** - OpenRouter disabled by default
3. **Gradual adoption** - enable via configuration or environment variables

### For New Installations

1. **Obtain OpenRouter API key** from https://openrouter.ai/
2. **Set environment variable**: `export OPENROUTER_API_KEY="your-key"`
3. **Enable provider**: Set `DEVSYNTH_PROVIDER=openrouter` or configure in YAML
4. **Select model**: Use `OPENROUTER_MODEL` environment variable or configuration

## Troubleshooting Guide

### Common Issues

#### Authentication Errors
- **Error**: `401 Unauthorized`
- **Cause**: Invalid or missing API key
- **Solution**: Verify `OPENROUTER_API_KEY` environment variable

#### Model Not Found
- **Error**: `404 Not Found` or `Invalid model`
- **Cause**: Model name not recognized by OpenRouter
- **Solution**: Check model name spelling and availability

#### Rate Limits
- **Error**: `429 Too Many Requests`
- **Cause**: Exceeded rate limits for model
- **Solution**: Implement retry logic, use circuit breaker, consider model switching

#### Network Issues
- **Error**: `5xx Server Error`
- **Cause**: OpenRouter service issues
- **Solution**: Use retry logic, fallback to other providers

### Debugging Tools

- **Request logging**: Enable debug logging for API requests
- **Response inspection**: Log full request/response for troubleshooting
- **Circuit breaker status**: Monitor circuit breaker state
- **Metrics tracking**: Use built-in metrics for performance monitoring

## Future Enhancements

### Potential Improvements

1. **Model recommendation engine** - suggest optimal models based on task
2. **Cost optimization** - automatic model selection based on cost/performance
3. **Multi-region support** - route to closest OpenRouter endpoint
4. **Caching layer** - cache frequently used embeddings and responses
5. **Batch processing** - support for batch API requests

### API Evolution

- **Monitor OpenRouter API changes** via their changelog
- **Version pinning** for stable integrations
- **Graceful degradation** for unsupported features

## References

- [OpenRouter API Documentation](https://openrouter.ai/docs/)
- [OpenRouter Models List](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/pricing)
- [Provider Harmonization Analysis](provider_harmonization_analysis.md)
- [Feature Parity Specification](provider_feature_parity.md)

This specification provides the foundation for implementing OpenRouter as a first-class provider in DevSynth, ensuring seamless integration with existing provider architecture while providing access to a wide variety of AI models through a unified interface.

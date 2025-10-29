---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:
- developer-guide
title: Error Handling Guidelines
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Developer Guides</a> &gt; Error Handling Guidelines
</div>

# Error Handling Guidelines

## Introduction

This document provides comprehensive guidelines for error handling in the DevSynth project. It aims to establish consistent, user-friendly error handling practices across all interfaces and components.

## Core Principles

### 1. User-Centered Error Messages

Error messages should be designed with the user in mind:
- **Clear**: Use plain language that explains what happened
- **Actionable**: Provide specific steps to resolve the issue
- **Contextual**: Relate the error to the user's current task
- **Respectful**: Avoid blaming the user or using technical jargon

### 2. Consistent Error Structure

All errors should follow a consistent structure:
- **Error Title**: A brief, clear description of the error
- **Error Details**: More specific information about what happened
- **Resolution Steps**: Concrete actions the user can take to resolve the issue
- **Additional Resources**: Links to documentation or support channels (when appropriate)

### 3. Progressive Disclosure

Implement progressive disclosure for error details:
- **Level 1**: Simple, user-friendly message for all users
- **Level 2**: More detailed explanation available on request
- **Level 3**: Technical details for developers (logs, stack traces, etc.)

### 4. Error Categorization

Categorize errors based on:
- **Severity**: Critical, Error, Warning, Info
- **Source**: User Input, System, External Service, etc.
- **Recovery Options**: Self-recoverable, User-recoverable, Non-recoverable

## Implementation Guidelines

### Error Hierarchy

All errors should inherit from the base `DevSynthError` class defined in `src/devsynth/exceptions.py`. The existing hierarchy provides a good foundation:

```text
DevSynthError
├── UserInputError
│   ├── ValidationError
│   ├── ConfigurationError
│   └── CommandError
├── SystemError
│   ├── InternalError
│   └── ResourceExhaustedError
├── AdapterError
│   ├── ProviderError
│   └── MemoryAdapterError
├── DomainError
│   ├── AgentError
│   ├── WorkflowError
│   └── ContextError
└── ApplicationError
    ├── PromiseError
    └── IngestionError
```

### Error Message Templates

Use consistent templates for error messages:

#### CLI Errors

```text
ERROR: <brief description>
<detailed explanation>

To resolve this issue:
- <step 1>
- <step 2>

For more information, see: <documentation link>
```

#### API Errors

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Brief user-friendly message",
    "details": "More detailed explanation",
    "resolution": ["Step 1", "Step 2"],
    "docs_url": "https://docs.example.com/errors/ERROR_CODE"
  }
}
```

### Error Logging

Follow these guidelines for error logging:
- Log all errors at appropriate levels (ERROR for actual errors, WARNING for potential issues)
- Include context information (user action, input data, system state)
- Don't log sensitive information (passwords, tokens, personal data)
- Use structured logging for machine-readable logs

#### Logging Configuration

DevSynth uses a centralized logging setup defined in `devsynth.logging_setup`.
Call `configure_logging()` at startup to initialize handlers. During runtime you
can set a request identifier and the current EDRR phase with `set_request_context(request_id, phase)`.
These values are automatically attached to all log records, enabling correlation
across components.

For standalone scripts, a helper at `scripts/utils/logging_setup.py` simplifies
this process and encourages consistent exception handling:

```python
import sys

from utils.logging_setup import setup_logging
from devsynth.exceptions import DevSynthError

logger = setup_logging(__name__)

def main() -> None:
    ...  # script logic


if __name__ == "__main__":
    try:
        main()
    except DevSynthError:
        logger.exception("Script failed")
        sys.exit(1)
    except Exception:  # pragma: no cover - unexpected errors
        logger.exception("Unexpected error")
        sys.exit(1)
```

This pattern ensures logs are routed through the DevSynth logger and that
errors are surfaced with clear, actionable messages.

## Error Handling Patterns

### Validation Errors

For input validation errors:
- Validate early, before processing begins
- Return all validation errors at once, not just the first one
- Be specific about what's wrong and how to fix it

Example:

```python
def process_config(config_data):
    errors = []

    if "api_key" not in config_data:
        errors.append("API key is required")

    if "max_retries" in config_data and not isinstance(config_data["max_retries"], int):
        errors.append("max_retries must be an integer")

    if errors:
        raise ValidationError(
            message="Invalid configuration",
            details={"errors": errors},
            resolution=["Check the documentation for required fields",
                       "Ensure all fields have the correct data type"]
        )

    # Process valid config...
```

### External Service Errors

For errors from external services:
- Translate technical errors into user-friendly messages
- Provide appropriate recovery options (retry, use alternative, etc.)
- Include diagnostic information for troubleshooting

### Graceful Degradation

Implement graceful degradation when possible:
- Continue with reduced functionality rather than failing completely
- Clearly communicate the limitations to the user
- Provide options to restore full functionality

## Error Telemetry

Guidelines for error reporting and telemetry:
- Collect aggregated error metrics to identify common issues
- Respect user privacy (anonymize data, get consent)
- Use error patterns to improve the product

## Practical Examples and Standards

### CLI Example

Handling a missing configuration file:

```bash
$ devsynth start --config nonexistent.yml
ERROR: Configuration file not found

To resolve this issue:
- Check that the path is correct
- Create the configuration file using `devsynth init`

For more information, see: https://docs.devsynth.com/errors/config-not-found
```

### API Example

Structured JSON error response:

```json
{
  "error": {
    "code": "CONFIG_NOT_FOUND",
    "message": "Configuration file not found",
    "details": "The provided path /tmp/nonexistent.yml does not exist",
    "resolution": ["Verify the path", "Create the file with the correct settings"],
    "docs_url": "https://docs.devsynth.com/errors/config-not-found"
  }
}
```

### User-Facing Error Message Standards

- Use plain language and avoid blaming the user.
- Provide clear steps to resolve the problem.
- Include a documentation link when possible.
- Indicate severity with consistent terminology: **Error**, **Warning**, **Info**.
- Present additional technical details only when requested.

### Visual Design Guidelines

- Display errors with high-contrast colors and icons that match the design system.
- In the CLI, use ANSI colors (`red` for errors, `yellow` for warnings).
- Web or GUI components should present errors in accessible alert boxes.
- Ensure all messages work with screen readers.
- Group related errors to reduce visual clutter.

### Testing Strategies for Error Scenarios

- **Unit Tests**: Validate error classes and message templates.
- **CLI Tests**: Verify exit codes and printed output for common failures.
- **API Tests**: Check JSON error structures and HTTP status codes.
- **Integration Tests**: Simulate failures from external services.
- **Visual Tests**: Capture screenshots to ensure consistent presentation.

## References

- [Nielsen Norman Group: Error Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/)
- [Microsoft Style Guide: Error Messages](https://docs.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/term-collections/error-messages)
## Implementation Status

.

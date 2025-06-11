---
title: "DevSynth User Guide"
date: "2025-06-01"
version: "1.0.0"
tags:
  - "user guide"
  - "documentation"
  - "commands"
  - "configuration"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-06-01"
---

# DevSynth User Guide

## Executive Summary

This comprehensive guide provides detailed information about using DevSynth, including all available commands, configuration options, and best practices. It serves as the primary reference for users working with the DevSynth platform.

See also: [Quick Start Guide](../getting_started/quick_start_guide.md), [Command Reference](#command-reference), [Configuration Options](#configuration-options)

## Table of Contents

- [Command Reference](#command-reference)
- [Configuration Options](#configuration-options)
- [Workflow Guide](#workflow-guide)
- [Best Practices](#best-practices)
- [Advanced Usage](#advanced-usage)

## Command Reference

DevSynth provides a command-line interface with the following commands:

### `init`

Initializes a new DevSynth project.

```bash
devsynth init [--path PATH]
```

**Options:**
- `--path PATH`: Path to initialize the project (default: current directory)

**Example:**
```bash
devsynth init --path ./my-new-project
```

**Details:**
This command creates a new project directory with the necessary structure for DevSynth to work with. It initializes configuration files and sets up the project environment.

### `analyze`

Analyzes requirements from a file or interactively.

```bash
devsynth analyze [--input FILE] [--interactive]
```

**Options:**
- `--input FILE`: Path to requirements file to analyze
- `--interactive`: Start an interactive session for requirement gathering

**Example:**
```bash
devsynth analyze --input requirements.md
```

**Details:**
This command processes requirements and provides insights about their completeness, consistency, and clarity. It helps identify potential issues before proceeding to specification generation.

### `analyze-code`

Analyzes a codebase to understand its architecture, structure, and quality.

```bash
devsynth analyze-code [--path PATH]
```

**Options:**
- `--path PATH`: Path to the codebase to analyze (default: current directory)

**Example:**
```bash
devsynth analyze-code --path ./my-project
```

**Details:**
This command analyzes any codebase (not just DevSynth projects) to provide insights about its architecture, structure, code quality, and test coverage. It can detect different architecture types (Hexagonal, MVC, Layered, Microservices) and identify potential issues and improvement opportunities. This is useful for understanding existing projects or evaluating the quality of generated code.

### `spec`

Generates specifications from requirements.

```bash
devsynth spec [--requirements-file FILE]
```

**Options:**
- `--requirements-file FILE`: Path to requirements file (default: requirements.md)

**Example:**
```bash
devsynth spec --requirements-file custom-requirements.md
```

**Details:**
This command creates detailed specifications based on the provided requirements. It expands high-level requirements into more detailed specifications that can be used for test generation.

### `test`

Generates tests from specifications.

```bash
devsynth test [--spec-file FILE]
```

**Options:**
- `--spec-file FILE`: Path to specifications file (default: specs.md)

**Example:**
```bash
devsynth test --spec-file custom-specs.md
```

**Details:**
This command creates test files based on the specifications. It generates unit tests, integration tests, and other test types as appropriate for the project.

### `code`

Generates implementation code from tests.

```bash
devsynth code
```

**Example:**
```bash
devsynth code
```

**Details:**
This command creates implementation code that satisfies the generated tests. It follows a test-driven development approach, ensuring that the code meets the requirements specified in the tests.

### `run`

Executes the generated code.

```bash
devsynth run [--target TARGET]
```

**Options:**
- `--target TARGET`: Specific target to run (e.g., unit-tests, integration-tests, all)

**Example:**
```bash
devsynth run --target unit-tests
```

**Details:**
This command runs the generated code or tests based on the specified target. It provides feedback on test results and code execution.

### `config`

Configures DevSynth settings.

```bash
devsynth config [--key KEY] [--value VALUE]
```

**Options:**
- `--key KEY`: Configuration key to set or view
- `--value VALUE`: Value to set for the configuration key

**Example:**
```bash
devsynth config --key model --value gpt-4
```

**Details:**
This command allows you to view or modify DevSynth configuration settings. It provides a way to customize the behavior of DevSynth for your specific needs.

## Configuration Options

DevSynth can be configured using the `config` command or by editing the configuration file directly. The following configuration options are available:

### LLM Configuration

| Key | Description | Default Value | Possible Values |
|-----|-------------|---------------|----------------|
| `model` | The LLM model to use | `gpt-3.5-turbo` | Any model supported by LM Studio |
| `temperature` | Creativity level (higher = more creative) | `0.7` | 0.0 - 1.0 |
| `max_tokens` | Maximum tokens for responses | `2000` | Any positive integer |
| `endpoint` | LM Studio API endpoint | `http://localhost:1234/v1` | Any valid URL |
| `openai_api_key` | OpenAI API key for using OpenAI models | None | Valid OpenAI API key |
| `serper_api_key` | Serper API key for web search functionality | None | Valid Serper API key |
| `memory_store_type` | Type of memory store to use | `memory` | `memory`, `file`, `chromadb` |

### Environment Variables and .env Files

DevSynth supports loading configuration from environment variables and `.env` files. This is especially useful for sensitive information like API keys.

#### Using Environment Variables

You can set environment variables directly in your shell:

```bash
# Set OpenAI API key
export OPENAI_API_KEY=your-api-key

# Set Serper API key
export SERPER_API_KEY=your-serper-key

# Set DevSynth-specific configuration
export DEVSYNTH_LLM_MODEL=gpt-4
export DEVSYNTH_LLM_TEMPERATURE=0.8
```

#### Using .env Files

Alternatively, you can create a `.env` file in your project directory:

```
# API Keys
OPENAI_API_KEY=your-api-key
SERPER_API_KEY=your-serper-key

# DevSynth Configuration
DEVSYNTH_LLM_MODEL=gpt-4
DEVSYNTH_LLM_TEMPERATURE=0.8
```

DevSynth will automatically load this file when it starts.

#### Environment Variable Naming

DevSynth-specific configuration variables use the `DEVSYNTH_` prefix:

| Environment Variable | Configuration Key |
|----------------------|------------------|
| `DEVSYNTH_MEMORY_STORE` | `memory_store_type` |
| `DEVSYNTH_MEMORY_PATH` | `memory_file_path` |
| `DEVSYNTH_MAX_CONTEXT_SIZE` | `max_context_size` |
| `DEVSYNTH_CONTEXT_EXPIRATION_DAYS` | `context_expiration_days` |
| `DEVSYNTH_LLM_PROVIDER` | `llm_provider` |
| `DEVSYNTH_LLM_API_BASE` | `llm_api_base` |
| `DEVSYNTH_LLM_MODEL` | `llm_model` |
| `DEVSYNTH_LLM_MAX_TOKENS` | `llm_max_tokens` |
| `DEVSYNTH_LLM_TEMPERATURE` | `llm_temperature` |
| `DEVSYNTH_LLM_AUTO_SELECT_MODEL` | `llm_auto_select_model` |

API keys use their standard environment variable names:

| Environment Variable | Configuration Key |
|----------------------|------------------|
| `OPENAI_API_KEY` | `openai_api_key` |
| `SERPER_API_KEY` | `serper_api_key` |

### Project Configuration

| Key | Description | Default Value | Possible Values |
|-----|-------------|---------------|----------------|
| `project_name` | Name of the project | Based on directory name | Any string |
| `project_description` | Description of the project | Empty string | Any string |
| `author` | Author of the project | System username | Any string |
| `license` | License for the project | `MIT` | Any valid license identifier |

### Development Configuration

| Key | Description | Default Value | Possible Values |
|-----|-------------|---------------|----------------|
| `test_framework` | Testing framework to use | `pytest` | `pytest`, `unittest` |
| `code_style` | Code style to follow | `pep8` | `pep8`, `google`, `numpy` |
| `documentation_style` | Documentation style | `google` | `google`, `numpy`, `sphinx` |

### Memory Configuration

DevSynth supports multiple memory store types for storing and retrieving memory items:

#### In-Memory Store

The default memory store type is `memory`, which stores all items in memory. This is fast but not persistent across sessions.

```bash
# Configure in-memory store
devsynth config --key memory_store_type --value memory
```

#### File-Based Store

The `file` memory store type uses a JSON file for persistent storage. This ensures that memory items are preserved across sessions.

```bash
# Configure file-based store
devsynth config --key memory_store_type --value file
devsynth config --key memory_file_path --value /path/to/memory/directory
```

#### ChromaDB Vector Store

The `chromadb` memory store type uses ChromaDB, a vector database, for persistent storage with semantic search capabilities. This is particularly useful for projects with large amounts of text data that benefit from semantic similarity search.

```bash
# Configure ChromaDB store
devsynth config --key memory_store_type --value chromadb
devsynth config --key memory_file_path --value /path/to/chromadb/directory
```

Key features of the ChromaDB memory store:

- **Semantic Search**: Search for memory items based on semantic similarity rather than exact matches
- **Vector Embeddings**: Automatically creates embeddings for text content to enable semantic search
- **Persistence**: Memory items are preserved across sessions
- **Scalability**: Efficiently handles large amounts of data
- **Caching Layer**: Reduces disk I/O operations by caching frequently accessed items
- **Version Tracking**: Maintains a history of changes to items over time
- **Optimized Embedding Storage**: Efficiently stores similar embeddings to reduce storage requirements

##### Caching

The ChromaDB memory store includes a caching layer that reduces disk I/O operations by storing frequently accessed items in memory. This improves performance when the same items are accessed multiple times.

##### Version Tracking

The ChromaDB memory store automatically tracks versions of items when they are updated. This allows you to:

- Retrieve the history of changes to an item
- Access specific versions of an item
- See when changes were made

Example usage in code:

```python
from devsynth.adapters.memory.memory_adapter import MemorySystemAdapter

# Initialize the memory system adapter
adapter = MemorySystemAdapter()
store = adapter.get_memory_store()

# Get all versions of an item
versions = store.get_versions("item-id")

# Get the history of an item
history = store.get_history("item-id")

# Retrieve a specific version of an item
version2 = store.retrieve_version("item-id", 2)
```

##### Optimized Embedding Storage

The ChromaDB memory store optimizes the storage of embeddings for similar content, reducing storage requirements and improving performance. This is particularly beneficial when storing multiple items with similar content.

## Workflow Guide

DevSynth follows an "expand, differentiate, refine" approach to software development:

### 1. Expand

In this phase, DevSynth takes high-level requirements and expands them into detailed specifications. This involves:

1. Analyzing requirements for completeness and consistency
2. Identifying implicit requirements
3. Expanding requirements into detailed specifications
4. Organizing specifications into a coherent structure

**Commands used in this phase:**
- `analyze`
- `spec`

### 2. Differentiate

In this phase, DevSynth differentiates the specifications into concrete tests and implementation plans. This involves:

1. Creating test cases for each specification
2. Defining test scenarios and edge cases
3. Establishing acceptance criteria
4. Planning the implementation structure

**Commands used in this phase:**
- `test`

### 3. Refine

In this phase, DevSynth refines the implementation based on the tests. This involves:

1. Generating implementation code
2. Running tests to verify the implementation
3. Refining the code to address any issues
4. Ensuring the code meets all requirements

**Commands used in this phase:**
- `code`
- `run`

## Best Practices

### Writing Effective Requirements

1. **Be specific**: Clearly state what the system should do
2. **Use consistent terminology**: Maintain consistent terms throughout requirements
3. **Focus on functionality**: Describe what the system should do, not how it should do it
4. **Include constraints**: Specify any limitations or constraints
5. **Prioritize requirements**: Indicate which requirements are essential

Example of a good requirement:
```
The system shall allow users to reset their password via email within 5 minutes of the request.
```

### Managing Projects

1. **Organize by feature**: Group related requirements by feature
2. **Version control**: Use version control for requirements and generated artifacts
3. **Iterative development**: Start with core requirements and expand incrementally
4. **Review generated artifacts**: Always review specifications, tests, and code
5. **Maintain traceability**: Ensure you can trace code back to requirements

### Optimizing LLM Usage

1. **Start with clear requirements**: Well-defined requirements lead to better results
2. **Adjust temperature**: Lower for precise tasks, higher for creative tasks
3. **Review and refine**: Iteratively improve generated artifacts
4. **Use appropriate context**: Provide relevant context for better results
5. **Balance token usage**: Be mindful of token limits

## Advanced Usage

### Custom Templates

DevSynth supports custom templates for specifications, tests, and code. You can create templates in the `tests/templates` directory:

- `tests/templates/spec_template.md`: Template for specifications
- `tests/templates/unit_test_template.py`: Template for test files
- `tests/templates/code_template.py`: Template for code files

### Integration with Version Control

DevSynth works well with version control systems like Git:

```bash
# Initialize Git repository
git init

# Add DevSynth files
git add requirements.md specs.md tests/ src/

# Commit changes
git commit -m "Initial DevSynth project"
```

### Custom Workflows

You can create custom workflows by combining DevSynth commands:

```bash
# Example custom workflow script
#!/bin/bash
devsynth analyze --input requirements.md
devsynth spec
devsynth test
devsynth code
devsynth run --target unit-tests
```

### Extending DevSynth

DevSynth follows a hexagonal architecture that makes it extensible. You can extend it by:

1. Creating custom adapters for different LLM providers
2. Implementing custom agents for specialized tasks
3. Adding new commands for additional functionality
4. Creating plugins for integration with other tools

For more information on extending DevSynth, refer to the [Architecture Documentation](architecture_documentation.md) and [API Reference](api_reference.md).

## Troubleshooting

### Common Issues

1. **Connection errors with LM Studio**:
   - Ensure LM Studio is running
   - Verify the endpoint configuration
   - Check network connectivity

2. **Out of memory errors**:
   - Reduce the model size
   - Optimize token usage
   - Increase system memory

3. **Poor quality output**:
   - Improve input requirements
   - Adjust temperature settings
   - Review and refine generated artifacts

## Current Limitations

Collaborative WSDE workflows, dialectical reasoning, and full EDRR automation are
still experimental. These features are off by default in `config/default.yml` and
may produce incomplete results. Automated code, test, and documentation generation
often requires manual review. See the
[Feature Status Matrix](../implementation/feature_status_matrix.md) for specifics.

### Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/ravenoak/devsynth/issues) for similar problems
2. Join the DevSynth community for support
3. Submit a detailed bug report with steps to reproduce the issue

## Conclusion

This user guide provides comprehensive information about using DevSynth effectively. By following the guidelines and best practices outlined here, you can maximize the benefits of AI-assisted software development with DevSynth.

For more detailed information about the architecture and internal workings of DevSynth, refer to the [Architecture Documentation](architecture_documentation.md).

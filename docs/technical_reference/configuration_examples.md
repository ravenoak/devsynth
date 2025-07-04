# DevSynth Configuration Examples

This document provides examples of common configuration patterns for DevSynth projects, focusing on Phase 1 features.

## Basic Configuration

A minimal configuration file for a Python project:

```yaml
# .devsynth/devsynth.yml
version: "1.0"
structure: "single_package"
language: "python"
goals: "Create a web application with user authentication and database integration"
```

Or in TOML format:

```toml
# pyproject.toml
[tool.devsynth]
version = "1.0"
structure = "single_package"
language = "python"
goals = "Create a web application with user authentication and database integration"
```

## Enabling Phase 1 Features

### EDRR Framework Configuration

Enable the EDRR framework with default settings:

```yaml
# .devsynth/devsynth.yml
features:
  edrr_framework: true
```

Enable the EDRR framework with custom settings:

```yaml
# .devsynth/devsynth.yml
features:
  edrr_framework: true
  micro_edrr_cycles: true
  recursive_edrr: true
edrr_settings:
  max_recursion_depth: 5
  enable_memory_integration: true
  termination_threshold: 0.9
  phase_weights:
    expand: 1.2
    differentiate: 1.0
    refine: 1.5
    retrospect: 0.8
```

### WSDE Multi-Agent Workflows Configuration

Enable WSDE collaboration with default settings:

```yaml
# .devsynth/devsynth.yml
features:
  wsde_collaboration: true
```

Enable WSDE collaboration with custom settings:

```yaml
# .devsynth/devsynth.yml
features:
  wsde_collaboration: true
  wsde_peer_review: true
  wsde_consensus_voting: true
  dialectical_reasoning: true
wsde_settings:
  team_size: 7
  peer_review_threshold: 0.8
  consensus_threshold: 0.7
  voting_weights:
    expertise: 0.7
    historical: 0.2
    primus: 0.1
```

### UXBridge Configuration

Enable WebUI using UXBridge:

```yaml
# .devsynth/devsynth.yml
features:
  uxbridge_webui: true
uxbridge_settings:
  default_interface: "webui"
  webui_port: 8501
```

Enable Agent API using UXBridge:

```yaml
# .devsynth/devsynth.yml
features:
  uxbridge_agent_api: true
uxbridge_settings:
  default_interface: "api"
  api_port: 8000
  enable_authentication: true
```

## Complete Phase 1 Configuration Example

A complete configuration example with all Phase 1 features enabled:

```yaml
# .devsynth/devsynth.yml
version: "1.0"
structure: "single_package"
language: "python"
goals: "Create a comprehensive web application with advanced features"
constraints: "Must be compatible with Python 3.11+"
priority: "Code quality and test coverage"

directories:
  source: ["src"]
  tests: ["tests"]
  docs: ["docs"]

features:
  wsde_collaboration: true
  dialectical_reasoning: true
  code_generation: true
  test_generation: true
  documentation_generation: true
  edrr_framework: true
  micro_edrr_cycles: true
  recursive_edrr: true
  wsde_peer_review: true
  wsde_consensus_voting: true
  uxbridge_webui: true
  uxbridge_agent_api: true

memory_store_type: "chromadb"
offline_mode: false

edrr_settings:
  max_recursion_depth: 4
  enable_memory_integration: true
  termination_threshold: 0.85
  phase_weights:
    expand: 1.2
    differentiate: 1.0
    refine: 1.3
    retrospect: 1.0

wsde_settings:
  team_size: 6
  peer_review_threshold: 0.75
  consensus_threshold: 0.65
  voting_weights:
    expertise: 0.65
    historical: 0.25
    primus: 0.1

uxbridge_settings:
  default_interface: "webui"
  webui_port: 8501
  api_port: 8000
  enable_authentication: true
```

## Configuration Validation

DevSynth validates your configuration and provides helpful error messages if there are issues. Some common validation rules:

- `max_recursion_depth` must be at least 1
- `team_size` must be at least 2
- `webui_port` and `api_port` must be between 1024 and 65535
- `phase_weights` and `voting_weights` must be dictionaries with appropriate values

If invalid values are provided, DevSynth will log a warning and use default values instead.

## Environment Variables

You can also configure DevSynth using environment variables, which take precedence over configuration files:

```bash
# Enable EDRR framework
export DEVSYNTH_FEATURE_EDRR_FRAMEWORK=true

# Set WSDE team size
export DEVSYNTH_WSDE_TEAM_SIZE=7

# Set UXBridge default interface
export DEVSYNTH_UXBRIDGE_DEFAULT_INTERFACE=webui
```

## Best Practices

1. **Start Simple**: Begin with a minimal configuration and add features as needed
2. **Use Feature Flags**: Enable only the features you need to avoid unnecessary complexity
3. **Customize Settings**: Adjust settings based on your project's specific requirements
4. **Version Control**: Keep your configuration file in version control to track changes
5. **Documentation**: Document any custom configuration settings in your project's README
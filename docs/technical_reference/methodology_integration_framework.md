---

author: DevSynth Team
date: '2025-07-07'
last_reviewed: "2025-07-10"
status: published
tags:

- technical-reference

title: 'Methodology Integration Framework: Supporting Diverse Development Approaches'
version: "0.1.0a1"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">Technical Reference</a> &gt; 'Methodology Integration Framework: Supporting Diverse Development Approaches'
</div>

# Methodology Integration Framework: Supporting Diverse Development Approaches

## Overview

This document outlines DevSynth's approach to supporting multiple development methodologies while maintaining its core "Expand, Differentiate, Refine, Retrospect" (EDRR) process. Rather than prescribing a specific workflow, DevSynth provides an adaptable framework that can integrate with any team's preferred way of working.

**Implementation Status:** The Sprint adapter integrates basic EDRR phase progression and retrospective metrics, but deeper automation and tooling are still pending. Outstanding tasks are documented in [issue 104](../../issues/Critical-recommendations-follow-up.md).

## Core Design Principles

1. **Methodology Agnosticism**: The core EDRR process functions independently of any specific development methodology
2. **Flexible Integration**: Ready-made adapters for common methodologies with customization options
3. **Configurable Cadence**: Support for time-boxed, continuous, or event-driven progression
4. **Extensible Framework**: Clear interfaces for creating custom methodology integrations
5. **Default with Options**: Sensible defaults that can be easily overridden


## The Methodology Adapter System

DevSynth implements a Methodology Adapter pattern that:

1. Maintains the logical sequence of the EDRR process
2. Allows flexible timing and progression through the phases
3. Integrates with external tools and processes
4. Provides templates for common methodologies
5. Supports creating custom implementations


### Available Methodology Adapters

DevSynth provides built-in support for several common development approaches:

#### 1. Agile Sprint Adapter

- Aligns EDRR phases with sprint ceremonies
- Configurable sprint duration (1-4 weeks)
- Integration with common Agile tools (Jira, GitHub Projects, etc.)
- Detailed in [Sprint-EDRR Integration](./sprint_edrr_integration.md)


#### 2. Kanban Flow Adapter

- Continuous progression through EDRR phases
- WIP limits for each phase
- Pull-based advancement
- Integration with Kanban boards and visualization tools
- Detailed in [Kanban-EDRR Integration](./kanban_edrr_integration.md)


#### 3. Milestone-Based Adapter

- Event-driven progression through EDRR phases
- Formal approval gates between phases
- Documentation generation for compliance
- Support for regulated environments
- Detailed in [Milestone-EDRR Integration](./milestone_edrr_integration.md)


#### 4. Ad-Hoc Processing Adapter

- On-demand execution of individual EDRR phases
- No prescribed timing or sequence
- Maximum flexibility for experimental or exploratory work
- Support for individual contributor workflows


#### 5. Custom Methodology Adapter

- Extensible base class for creating custom adapters
- Configuration-driven customization
- Documentation for creating adapters
- Example implementations

### Project Management Tool Adapters

DevSynth also ships with scaffolding for integrating external project
tracking systems. These adapters allow methodology progress to be
synchronized with tools that teams already use:

- **GitHub Project Adapter** – synchronizes EDRR tasks with GitHub
  Projects boards. Configure via `config/github_project.yml`.
- **Jira Adapter** – provides hooks for creating and transitioning Jira
  issues. Configure via `config/jira.yml`.

Both adapters currently focus on configuration loading and provide
placeholders for future network operations.


## Configuring Your Preferred Methodology

### Configuration in `.devsynth/project.yaml`

The project's methodology preferences are specified in the `.devsynth/project.yaml` file:

```yaml
methodologyConfiguration:
  # Choose from: "sprint", "kanban", "milestone", "adhoc", or "custom"
  type: "sprint"

  # General settings (available for all methodologies)
  phases:
    expand:
      skipable: false
      customHooks: ["pre-expand.sh", "post-expand.sh"]
    differentiate:
      skipable: true
    refine:
      skipable: false
    retrospect:
      skipable: false
      customHooks: ["lessons-learned-template.md"]

  # Methodology-specific settings
  settings:
    # Sprint-specific settings (when type is "sprint")
    sprintDuration: 2 # weeks
    ceremonyMapping:
      planning: "retrospect.iteration_planning"
      dailyStandup: "phase_progression_tracking"
      review: "refine.outputs_review"
      retrospective: "retrospect.process_evaluation"

    # Kanban-specific settings (when type is "kanban")
    wipLimits:
      expand: 3
      differentiate: 2
      refine: 2
      retrospect: 1

    # Milestone-specific settings (when type is "milestone")
    approvalRequired:
      afterExpand: true
      afterDifferentiate: true
      afterRefine: true
      afterRetrospect: false
    approvers: ["tech-lead", "product-owner"]

    # Custom settings (when type is "custom")
    customAdapterPath: "./custom_methodology_adapter.py"
    customAdapterSettings:
      # Any custom settings needed by your adapter
```

### CLI Configuration

Methodology settings can be configured and updated via the CLI:

```bash

# Set the methodology type

devsynth config set methodology.type sprint

# Configure phase-specific settings

devsynth config set methodology.phases.expand.skipable false

# Configure methodology-specific settings

devsynth config set methodology.settings.sprintDuration 2
```

## Implementing a Custom Methodology Adapter

To create a custom methodology adapter for your team's specific needs:

1. Create a new Python class that extends `BaseMethodologyAdapter`
2. Implement the required interface methods
3. Register your adapter with DevSynth
4. Configure your project to use the custom adapter


### Example Custom Adapter

```python
from devsynth.methodology.base import BaseMethodologyAdapter

class MyTeamMethodologyAdapter(BaseMethodologyAdapter):
    """Custom methodology adapter for my team's workflow."""

    def __init__(self, config):
        super().__init__(config)
        # Initialize any custom state

    def before_expand(self, context):
        # Custom logic before entering Expand phase
        pass

    def after_expand(self, context, results):
        # Custom logic after completing Expand phase
        pass

    # Implement other phase hooks...

    def should_progress_to_next_phase(self, current_phase, context, results):
        # Custom logic to determine if ready to move to next phase
        return True
```

Register your custom adapter in your project configuration:

```yaml

# In .devsynth/project.yaml

methodologyConfiguration:
  type: "custom"
  customAdapterPath: "./my_team_adapter.py"
  customAdapterClass: "MyTeamMethodologyAdapter"
```

## Integration with External Tools

Each methodology adapter includes built-in integration capabilities with common external tools:

### Tool Integration Configuration

```yaml

# In .devsynth/project.yaml

methodologyConfiguration:
  type: "sprint"
  toolIntegration:
    jira:
      enabled: true
      projectKey: "MYPROJECT"
      sprintField: "customfield_10001"
    github:
      enabled: true
      projectBoard: "My Project Board"
    gitlab:
      enabled: false
    custom:
      enabled: true
      webhookUrl: "https://my-custom-tool.example.com/webhook"
      eventMappings:
        "phase.started": "task.status.update"
        "phase.completed": "milestone.complete"
```

## Current Limitations

- Only a basic Sprint adapter is implemented; other methodologies are planned.
- External tool integrations beyond Jira are still experimental.


## Conclusion

DevSynth's Methodology Adapter System allows teams to leverage the power of the EDRR process while working within their preferred development methodology. By separating the core process from its timing and integration aspects, DevSynth provides the flexibility needed to support diverse development approaches while maintaining the benefits of its structured, iterative approach to software development.

Whether your team uses Agile sprints, Kanban flow, milestone-based development, or a completely custom approach, DevSynth can adapt to your way of working rather than forcing you to adapt to it.

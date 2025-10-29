---

title: "EDRR Command User Guide"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "user-guide"
status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; EDRR Command User Guide
</div>

# EDRR Command User Guide

## Overview

The `EDRR-cycle` command is a powerful tool in the DevSynth CLI that executes an EDRR (EDRR) cycle. This structured approach to problem-solving and development helps you systematically tackle complex tasks by breaking them down into distinct phases.

This implementation uses the Enhanced EDRR Coordinator which provides improved phase transitions, quality metrics, and safeguards against infinite loops.

## Command Syntax

```bash
devsynth EDRR-cycle [OPTIONS]
```

## Options

| Option | Description | Default |
|--------|-------------|---------|
| `--manifest TEXT` | Path to a manifest file defining the task and constraints | None |
| `--prompt TEXT` | A text prompt describing the task | None |
| `--context TEXT` | Additional context for the prompt | None |
| `--max-iterations INTEGER` | Maximum number of iterations for the cycle | 3 |
| `--auto BOOLEAN` | Whether to automatically progress through phases | True |

**Note**: Either `--manifest` or `--prompt` must be provided.

## EDRR Phases

The EDRR consists of four phases:

1. **Expand**: Generate a wide range of ideas, approaches, and potential solutions.
2. **Differentiate**: Categorize and evaluate the ideas from the Expand phase.
3. **Refine**: Develop and improve the selected approaches.
4. **Retrospect**: Reflect on the process, outcomes, and lessons learned.

## Enhanced Features

The Enhanced EDRR Coordinator provides several improvements over the standard EDRR Coordinator:

- **Quality-Based Phase Transitions**: Automatically transitions between phases based on quality metrics.
- **Comprehensive Metrics Collection**: Collects detailed metrics for each phase.
- **Infinite Loop Prevention**: Implements safeguards to prevent infinite loops during automatic phase transitions.
- **Improved Error Handling**: Provides better error handling and reporting.

## Examples

### Running from a Manifest File

```bash
devsynth EDRR-cycle --manifest .devsynth/project.yaml
```

This command starts an EDRR using the task definition in the manifest file.

### Running from a Prompt

```bash
devsynth EDRR-cycle --prompt "Improve error handling in the API endpoints"
```

This command starts an EDRR with the given prompt as the task description.

### Adding Context to a Prompt

```bash
devsynth EDRR-cycle --prompt "Optimize database queries" --context "Focus on reducing N+1 queries"
```

This command starts an EDRR with additional context for the prompt.

### Controlling Iterations

```bash
devsynth EDRR-cycle --prompt "Refactor the authentication system" --max-iterations 5
```

This command sets the maximum number of iterations for the cycle to 5.

### Disabling Automatic Phase Transitions

```bash
devsynth EDRR-cycle --prompt "Implement authentication" --auto false
```

This command disables automatic phase transitions, requiring manual progression through phases.

## Output

The command provides progress information during execution and generates a final report at the end. The report includes:

- Key insights from the EDRR
- Recommended next steps
- Quality metrics for each phase
- Detailed results from each phase

## Best Practices

1. **Be Specific in Prompts**: Provide clear, specific prompts to get better results.
2. **Use Context for Clarification**: Add context to provide additional information or constraints.
3. **Review Phase Metrics**: Check the metrics for each phase to understand the quality of the results.
4. **Adjust Max Iterations**: Increase the maximum iterations for complex tasks.
5. **Consider Manual Mode**: For more control, disable automatic phase transitions.

## Troubleshooting

### Common Issues

1. **Slow Progress**: For complex tasks, the cycle may take longer to complete. Consider increasing the maximum iterations.
2. **Low Quality Results**: If the results don't meet your expectations, try providing more specific prompts and context.
3. **Errors During Execution**: Check the error messages for details. Most errors are related to input validation or resource limitations.

### Getting Help

For more information, use the help command:

```bash
devsynth EDRR-cycle --help
```

## Related Commands

- `devsynth init`: Initialize a new project
- `devsynth spec`: Generate specifications from requirements
- `devsynth test`: Generate tests from specifications
- `devsynth code`: Generate code from tests
## Implementation Status

.

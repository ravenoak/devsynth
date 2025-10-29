---
title: "Test Generation"
date: "2025-08-17"
version: "0.1.0a1"
tags:
  - testing
  - user-guide
status: "draft"
author: "DevSynth Team"
last_reviewed: "2025-08-17"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; Test Generation
</div>

# Test Generation

The Test agent can scaffold integration tests for single- or multi-module
projects. Provide a list of module paths to create a placeholder test within an
output directory for each module.

```python
from devsynth.application.agents.test import TestAgent

agent = TestAgent()
result = agent.process(
    {
        "modules": ["core", "utils.parsers"],
        "integration_output_dir": "tests/integration/generated",
    }
)
print(result["integration_tests"].keys())
# dict_keys(['core/test_core.py', 'utils/parsers/test_parsers.py'])
```

The generated files contain a simple assertion so they pass immediately. Use
`run_generated_tests` to execute them:

```python
agent.run_generated_tests(Path("tests/integration/generated"))
```

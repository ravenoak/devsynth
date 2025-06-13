# DevSynth Agent Adapter Example

This example demonstrates how to use the `AgentAdapter` directly from Python
alongside the standard DevSynth CLI commands.

## Steps

1. **Initialize the project**
   ```bash
   devsynth init --path .
   ```
   This creates the `.devsynth/project.yaml` configuration.

2. **Run the CLI workflow**
   ```bash
   devsynth spec --requirements-file requirements.md
   devsynth test
   devsynth code
   ```

3. **Run the adapter example**
   ```bash
   python adapter_example.py
   ```
   The script creates a team, adds an agent, and processes a simple task using
   the `AgentAdapter` API.

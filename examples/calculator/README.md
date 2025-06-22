# DevSynth Calculator Example

This example demonstrates how to use DevSynth to generate a simple calculator project.
It walks through project initialization, specification generation, test creation, implementation, and running the final code.

## Steps

1. **Initialize the project**
   ```bash
   devsynth init --path .
   ```
   This creates the `.devsynth/project.yaml` configuration.

2. **Define requirements**
   Edit `requirements.md` with the desired functionality.

3. **Generate specifications**
   ```bash
   devsynth spec --requirements-file requirements.md
   ```

4. **Generate tests**
   ```bash
   devsynth test
   ```

5. **Generate code**
   ```bash
   devsynth code
   ```

6. **Run the project**
   ```bash
   devsynth run-pipeline
   ```

The files in this directory show the final result after running these commands.

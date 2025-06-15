# DevSynth Full Workflow Example

This example demonstrates the full DevSynth workflow using a simple word counter project. It covers project initialization, specification and test generation, code creation, the refactor workflow, and reviewing the generated output.

## Steps

1. **Initialize the project**
   ```bash
   devsynth init --path .
   ```
   This creates the `.devsynth/project.yaml` configuration.

2. **Add requirements**
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

6. **Run the refactor workflow**
   ```bash
   devsynth refactor
   ```
   This analyzes the project and suggests further steps.

7. **Review and run**
   Inspect `specs.md`, the `tests/` directory, and the `src/` implementation. Then run:
   ```bash
   devsynth run
   ```

The files in this directory show the final result after executing these commands.

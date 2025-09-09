# DevSynth End-to-End CLI Example

This example walks through a typical DevSynth workflow using only the command line. It demonstrates how to go from requirements to working code using `devsynth` commands.

## Requirements
- Poetry environment with minimal extras:
  - `poetry install --with dev --extras minimal`
- See also: docs/examples/requirements.md

## Steps

1. **Initialize the project**
   ```bash
   devsynth init --path .
   ```
   This sets up `.devsynth/project.yaml`.

2. **Write requirements**
   Edit `requirements.md` with the desired features.

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
   Review the output in `src/` and `tests/`.

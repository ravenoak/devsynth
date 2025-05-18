# Basic Usage

This guide provides basic usage examples for DevSynth.

## Initialize a Project
```bash
devsynth init --path ./my-project
cd my-project
```

## Define Requirements
Create a `requirements.md` file with your requirements.

## Generate Specifications, Tests, and Code
```bash
devsynth spec --requirements-file requirements.md
devsynth test
devsynth code
```

## Run the Project
```bash
devsynth run
```

See the [User Guide](../user_guides/user_guide.md) for more advanced usage.


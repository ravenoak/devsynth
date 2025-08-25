# DevSynth End-to-End WebUI Example

This example mirrors the CLI workflow but uses the experimental WebUI. It shows how to complete a project from requirements to running code through the browser interface.

## Requirements
- Poetry environment with the webui extra installed:
  - `poetry install --with dev --extras "minimal webui"`
- See also: docs/examples/requirements.md

## Steps

1. **Start the WebUI**
   ```bash
   devsynth webui
   ```
   Open the displayed URL in your browser.

2. **Create a new project**
   Use the *Onboarding* page to initialize your project and generate `.devsynth/project.yaml`.

3. **Enter requirements**
   Navigate to the *Requirements* page and add your project requirements.

4. **Generate specs and tests**
   Use the *Generate Specs* and *Generate Tests* buttons in the WebUI.

5. **Generate code**
   Click *Generate Code* to produce the implementation.

6. **Run the pipeline**
   Use the *Run* button to execute the generated code and tests.

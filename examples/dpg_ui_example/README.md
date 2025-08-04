# DevSynth Dear PyGui UI Example

This example demonstrates a full workflow using the experimental Dear PyGui interface.

## Steps

1. **Install DevSynth with GUI support**
   ```bash
   pip install 'devsynth[gui]'
   ```

2. **Initialize a demo project**
   ```bash
   devsynth init demo_project
   cd demo_project
   ```

3. **Launch the Dear PyGui interface**
   ```bash
   devsynth dpg
   ```

4. **Run the workflow**
   Use the UI to execute `spec`, `test`, and `code` or run the full `run-pipeline` command.

5. **Hello World**
   The [hello_world.py](hello_world.py) script shows direct usage of `DearPyGUIBridge`:
   ```bash
   python hello_world.py
   ```

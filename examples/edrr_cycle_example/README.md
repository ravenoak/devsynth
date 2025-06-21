# DevSynth EDRR Cycle Example

This walkthrough shows how to run a full Expand-Differentiate-Refine-Retrospect cycle.

## Steps

1. **Create a manifest**
   Save the following as `manifest.yaml`:
   ```yaml
   project: edrr-demo
   ```

2. **Run the edrr-cycle command**
   ```bash
   devsynth edrr-cycle manifest.yaml
   ```
   The command orchestrates the EDRR cycle using the provided manifest and reports the results.

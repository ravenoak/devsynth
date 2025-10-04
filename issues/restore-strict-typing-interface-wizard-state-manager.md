# Restore strict typing for `devsynth.interface.wizard_state_manager`

## Summary

The wizard state manager wires Streamlit session values through untyped
callbacks. The strict typing sweep defers this module until typed `WizardState`
contracts are introduced.

## Tasks

- [ ] Define explicit TypedDict/Protocol contracts for wizard state payloads.
- [ ] Annotate manager methods and callback parameters.
- [ ] Remove the override and update the typing relaxation log.

## Evidence

- See TODO `typing-interface-wizard-state-manager` in `pyproject.toml`.

# Auto-generated integration tests

DevSynth can scaffold integration tests to highlight missing coverage while teams iterate on APIs.

## Workflow

1. Use `scaffold_integration_tests` or `write_scaffolded_tests` in `src/devsynth/testing/generation.py` to create placeholder tests. The generated modules are marked with `pytest.mark.skip` so the suite stays green.
2. Review each scaffolded file:
   - Replace the placeholder body with real assertions.
   - Remove the `pytest.mark.skip` marker when the test is complete.
3. Use the prompt in `src/devsynth/testing/prompts.py` as guidance when authoring tests or when generating them automatically. The prompt emphasizes edge cases such as empty inputs, extreme values, permission errors, and network failures.
4. Run `poetry run devsynth run-tests --speed=fast` and `poetry run pre-commit run --files ...` before submitting changes.

This process ensures that auto-generated tests receive human oversight and evolve into reliable integration coverage.

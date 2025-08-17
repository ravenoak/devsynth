# Auto-generated integration tests

DevSynth can scaffold integration tests to highlight missing coverage while teams
iterate on APIs. When the testing agent receives project context it derives
likely integration targets and scaffolds placeholder modules for them
automatically.

## Workflow

1. Use `scaffold_integration_tests` or `write_scaffolded_tests` in
   `src/devsynth/testing/generation.py` to create placeholder tests. The
   `TestAgent` also invokes these helpers, deriving file names from project
   descriptions when explicit names are absent.
2. Review each scaffolded file:
   - Replace the placeholder body with real assertions.
   - Add `pytest.mark.skip` if temporary suppression of failures is needed and
     remove the marker once the test is implemented.
3. Use the prompt in `src/devsynth/testing/prompts.py` as guidance when authoring tests or when generating them automatically. The prompt emphasizes edge cases such as empty inputs, extreme values, permission errors, and network failures.
4. Run `poetry run devsynth run-tests --speed=fast` and `poetry run pre-commit run --files ...` before submitting changes.

This process ensures that auto-generated tests receive human oversight and evolve into reliable integration coverage.

## Mocking Optional Services

Some providers, such as LM Studio, may be unavailable during local testing. Use
`pytest.importorskip("lmstudio")` to skip tests when the optional SDK is not
installed and rely on the `lmstudio_service` fixture to emulate the HTTP API. The
fixture lives under `tests/fixtures/` and returns deterministic responses for
model listing, text generation, and embeddings so tests can run without a real
LM Studio instance.

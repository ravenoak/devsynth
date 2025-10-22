# Environment Extras and Optional Dependencies

DevSynth relies on Poetry extras to keep optional dependencies lightweight while
still making key scenarios reproducible. Use the following checklists when
preparing a workstation or CI agent.

## Baseline for running the test suite

Run the command below **before executing any tests**. It installs the
development dependencies as well as the optional extras needed by fast and
medium suites:

```bash
poetry install --with dev --extras "tests retrieval chromadb api"
```

Running the suite without these extras will cause collection failures for
resource-gated tests and missing-type stubs.

## Authentication and Argon2 support

Password hashing utilities in `devsynth.security.authentication` use Argon2.
The dependency is provided by the `security` extra to avoid forcing the heavier
cryptography stack on installations that do not need authentication. When
authentication is enabled (the default), ensure the extra is installed:

```bash
poetry install --with dev --extras "security"
# or, if Poetry is not available
pip install "devsynth[security]"
```

If Argon2 is not installed and `DEVSYNTH_AUTHENTICATION_ENABLED` is left at its
default of `true`, authentication calls raise an ImportError with guidance to
install the extra. Disable the feature explicitly by exporting
`DEVSYNTH_AUTHENTICATION_ENABLED=false` when working in environments that cannot
install the dependency.

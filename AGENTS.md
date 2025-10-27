# AGENTS.md

## Project Snapshot

**What is DevSynth?**
DevSynth implements agent services under `src/devsynth/` and supporting scripts under `scripts/`. It values clarity, collaboration, and dependable automation. For architecture and policy references, see `docs/` and `CONTRIBUTING.md`.

> **NOTE:** All GitHub Actions workflows are temporarily disabled and must be triggered manually via `workflow_dispatch` until the `v0.1.0a1` tag is created (see `docs/tasks.md` item 10.1). No `push`, `pull_request`, or `schedule` triggers may be added during this period. The CI workflow provides smoke, unit+integration, and typing+lint jobs with concurrency controls and caches for Poetry, pip, and `.pytest_cache`; on failures it uploads `test_reports/`, `htmlcov/`, `coverage.json`, and `diagnostics/doctor_run.txt`.

## Setup

**How do I prepare my environment?**
1. Ensure Python 3.12 is active and Poetry created a virtual environment (enforced via the committed `poetry.toml`):
   ```bash
   python --version
   poetry env info --path  # must print the virtualenv path
   ```
   If `poetry env info --path` prints nothing or points elsewhere, recreate the environment:
   ```bash
   poetry env use 3.12 && poetry install --with dev --extras tests retrieval chromadb api
   ```
2. Provision the environment:
   ```bash
   bash scripts/install_dev.sh      # general setup (auto-installs go-task)
   bash scripts/codex_setup.sh      # Codex agents (finishes <15m, warns >10m)
   task --version                   # verify Taskfile is available
   ```
   The install script downloads `go-task` to `$HOME/.local/bin` and adds it to
   the `PATH` for subsequent steps. These checks are mirrored in
   [scripts/install_dev.sh](scripts/install_dev.sh),
   the release guide [docs/release/0.1.0-alpha.1.md](docs/release/0.1.0-alpha.1.md),
   and the CI workflow [.github/workflows/ci.yml](.github/workflows/ci.yml).
   - Always inspect `scripts/codex_setup.sh` and `scripts/codex_maintenance.sh`
     first when diagnosing environment failures. Provisioning calls them as
     `scripts/codex_setup.sh || touch CODEX_ENVIRONMENT_SETUP_FAILED` for new
     containers and `scripts/codex_maintenance.sh || touch
     CODEX_ENVIRONMENT_MAINTENANCE_FAILED` for cached resumes. Both scripts now
     self-install Poetry via `pipx` when missing, enforce Poetry 2.2.1 (to match
     the lock file), normalize the project version from either `[tool.poetry]`
     or `[project]`, and run `poetry check` up front so lock-file drift is
     reported immediately.
   - On a cached container rerun the lighter maintenance script directly to
     resync dependencies and run fast health probes:
     ```bash
     bash scripts/codex_maintenance.sh
     ```
     Successful runs remove the corresponding `CODEX_ENVIRONMENT_*_FAILED`
     marker files so the workspace reflects its current status.
3. Install dependencies with development and test extras. Use `poetry run` for all Python invocations (or `task` for Taskfile targets) so commands run inside the Poetry-managed virtualenv.

   Optional test extras map to resource markers:
   - `poetry install --extras retrieval` provides `kuzu` and `faiss-cpu` for tests marked with `requires_resource("kuzu")` or `requires_resource("lmdb")`.
   - `poetry install --extras chromadb` enables ChromaDB-specific tests marked `requires_resource("chromadb")`.
   - `poetry install --extras memory` pulls the full memory stack if running all back-end tests.

## Testing

**How do I keep the build green?**
Codex-style agents run commands iteratively until all tests pass:
```bash
poetry run pre-commit run --files <changed>
poetry run devsynth run-tests --speed=<fast|medium|slow>
poetry run python tests/verify_test_organization.py
poetry run python scripts/verify_test_markers.py
poetry run python scripts/verify_requirements_traceability.py
poetry run python scripts/verify_version_sync.py
```
CI runs `poetry run python scripts/verify_test_markers.py` to ensure each test carries a speed marker.
`tests/conftest.py` provides an autouse `global_test_isolation` fixture; avoid setting environment variables at import time. Use speed markers `fast`, `medium`, or `slow` from `tests/conftest_extensions.py` and combine them with context markers when needed. Optional services should be guarded with environment variables like `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE` or `pytest.importorskip`.

## Conventions

**What practices guide contributions?**
- Begin with the Socratic checklist: *What is the problem?* and *What proofs confirm the solution?*
- Follow the specification-first BDD workflow: draft specs in `docs/specifications/` and pair them with failing features under `tests/behavior/features/` before implementation.
- Use [Conventional Commits](https://www.conventionalcommits.org/) with a one-line summary and descriptive body, then open a pull request with `make_pr` that summarizes changes and test evidence.
- Use system time when recording the current date or datetime.
- Honor all policies under `docs/policies/` (security, audit, etc.), including the [Dialectical Audit Policy](docs/policies/dialectical_audit.md); resolve `dialectical_audit.log` before submission.
- Use the in-repo issue tracker (`issues/`; see `issues/README.md`).
- Consult `docs/release/0.1.0-alpha.1.md` for release steps and `.github/workflows/` for automation guidelines.

## Directory-Specific Guidance

**What additional guidance applies to specific directories?**

### Source Code (`src/devsynth/`)
- Follow the specification-first BDD workflow: draft specs in `docs/specifications/` and failing features in `tests/behavior/features/` before writing code
- Adhere to the [Security Policy](docs/policies/security.md) and [Dialectical Audit Policy](docs/policies/dialectical_audit.md)
- All source changes should be accompanied by appropriate tests

### Testing (`tests/`)
- Each test must include exactly one speed marker (`fast`, `medium`, `slow`) from `tests/conftest_extensions.py`
- Guard optional services with `pytest.importorskip` and environment variables like `DEVSYNTH_RESOURCE_<NAME>_AVAILABLE`
- The `tests/conftest.py` provides an autouse `global_test_isolation` fixture; avoid setting environment variables at import time
- Agent API tests require the `api` extra: `poetry install --extras api`

### Documentation (`docs/`)
- Follow [Documentation Policies](docs/policies/documentation_policies.md) for style and structure
- Capture new requirements in `docs/specifications/` before implementation
- Honor the [Dialectical Audit Policy](docs/policies/dialectical_audit.md) and resolve `dialectical_audit.log`
- Use system time when recording current date or datetime

## Further Reading

**Where can I learn more?**
- Detailed API conventions: `docs/api_reference.md`
- Additional architecture and policy guides: `docs/`
- Contribution guidelines: `CONTRIBUTING.md`

## Cursor IDE Integration

**How do I use Cursor IDE effectively with DevSynth?**

### Development Workflow Integration
1. **EDRR-Enhanced Development**: Use Cursor Rules to guide each EDRR phase (Expand, Differentiate, Refine, Retrospect)
2. **Specification-Driven Coding**: Leverage Cursor Commands for SDD workflow (Specify, Plan, Tasks, Implement)
3. **Multi-Agent Coordination**: Use Cursor Modes for different agent personas (EDRRImplementer, SpecArchitect)

### Cursor Configuration Structure
```
.cursor/
├── rules/                           # Always-apply and auto-attach rules
│   ├── 00-architecture.mdc          # Project constitution and architecture
│   ├── 00-project-core.md           # Core project philosophy and setup
│   ├── 01-edrr-framework.mdc        # EDRR phase guidance and structured thinking
│   ├── 01-testing-standards.md     # Comprehensive testing standards
│   ├── 02-bdd-workflow.md           # BDD workflow with Gherkin features
│   ├── 02-specification-driven.mdc  # SDD + BDD integration
│   ├── 03-security-compliance.md    # Security requirements
│   ├── 03-testing-philosophy.mdc    # Testing philosophy and practices
│   ├── 04-code-style.md             # Code style and formatting standards
│   ├── 04-security-compliance.mdc   # Security compliance rules
│   ├── 05-dialectical-reasoning.mdc # Dialectical audit policy
│   ├── 05-documentation.md          # Documentation standards
│   ├── 06-commit-workflow.md        # Git commit and workflow standards
│   ├── 07-cursor-rules-management.md # Cursor rules management
│   ├── 07-poetry-environment.md     # Poetry dependency and environment management
│   └── workflows/                    # Workflow-specific guidance
│       ├── adding-feature.md        # Feature development workflow
│       ├── fixing-bug.md            # Bug fixing workflow
│       └── running-tests.md         # Testing workflow
├── commands/                        # Structured workflow commands
│   ├── code-review.md               # Comprehensive code review
│   ├── differentiate-phase.md       # Analysis and comparison workflows
│   ├── expand-phase.md              # Divergent thinking workflows
│   ├── generate-specification.md    # SDD specification creation
│   ├── generate-test-suite.md       # Test suite generation
│   ├── refine-phase.md              # Implementation and optimization
│   ├── retrospect-phase.md          # Learning and improvement
│   └── validate-bdd-scenarios.md    # BDD scenario validation
├── modes.json                       # Custom Cursor modes configuration
├── README.md                        # Cursor integration overview
├── CURSOR_SETUP.md                  # Detailed setup instructions
├── CURSOR_INTEGRATION.md            # Integration troubleshooting
└── integration-test.md              # Integration testing guidance
```

### Cursor Rules Application

#### Core Rules (Always Applied)
- **00-architecture.mdc**: Project constitution and core architectural principles - always active
- **00-project-core.md**: Core project philosophy, setup, and development workflow - always active
- **01-edrr-framework.mdc**: EDRR methodology phase guidance and structured thinking - always active
- **02-specification-driven.mdc**: Specification-Driven Development (SDD) + BDD integration - always active

#### Context-Specific Rules (Auto-Attach)
- **01-testing-standards.md**: Applied when working with test files - comprehensive testing standards
- **02-bdd-workflow.md**: Applied when working with BDD features and step definitions
- **03-security-compliance.md**: Applied to all source code - security requirements and validation
- **03-testing-philosophy.mdc**: Applied when working with tests - testing philosophy and practices
- **04-code-style.md**: Applied to all Python code - formatting and style standards
- **07-poetry-environment.md**: Applied when working with dependency files - Poetry and environment management

#### Specialized Rules (Manual Invocation)
- **04-security-compliance.mdc**: Deep security analysis - invoke with @security-analysis
- **05-dialectical-reasoning.mdc**: Dialectical reasoning for decisions - invoke with @dialectical-audit
- **06-commit-workflow.md**: Git workflow guidance - invoke with @commit-guidance

### Cursor Commands Usage

#### EDRR Workflow Commands
- **/expand-phase**: Generate multiple diverse approaches and explore alternatives
- **/differentiate-phase**: Compare options, evaluate against requirements, identify trade-offs
- **/refine-phase**: Implement chosen solution with comprehensive testing and optimization
- **/retrospect-phase**: Analyze outcomes, capture learnings, suggest improvements

#### Specification and Testing Commands
- **/generate-specification**: Create comprehensive SDD specifications and BDD scenarios
- **/validate-bdd-scenarios**: Validate Gherkin syntax, content quality, and implementation feasibility
- **/generate-test-suite**: Create comprehensive test coverage (unit, integration, BDD)
- **/code-review**: Perform comprehensive code quality assessment and improvement suggestions

#### Development Workflow Commands
- **/fix-bdd-syntax**: Fix common BDD/Gherkin syntax issues
- **/add-speed-markers**: Add appropriate speed markers to tests
- **/update-specifications**: Update specifications to reflect implementation changes

### Practical Cursor IDE Usage

#### Daily Development Workflow
1. **Environment Setup**: Ensure you're in the Poetry environment (`poetry run` prefix for all commands)
2. **Context Loading**: Open project in Cursor to automatically load rules and context
3. **Specification Check**: Review relevant specifications in `docs/specifications/`
4. **EDRR Process**: Use Cursor commands for structured development
5. **Quality Gates**: Run tests and validation before committing

#### Common Cursor Interactions
- **Chat Interface**: Use `/expand-phase`, `/differentiate-phase`, etc. for structured assistance
- **Composer Mode**: Leverage Cursor's composer for complex implementations with rule guidance
- **Code Generation**: Apply EDRR rules for systematic code generation and review
- **Testing Integration**: Use Cursor's terminal integration for running tests within the environment

#### Platform-Specific Setup

**macOS (Current Environment)**:
```bash
# 1. Verify Python 3.12 installation
/opt/homebrew/bin/python3.12 --version  # Should show 3.12.x

# 2. Setup Poetry environment
poetry env use /opt/homebrew/bin/python3.12
poetry install --with dev --extras "tests retrieval chromadb api"

# 3. Verify Cursor integration
poetry run python scripts/verify_cursor_integration.py

# 4. Enable optional resources
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
```

**Linux**:
```bash
# 1. Install Python 3.12 and Poetry
sudo apt update && sudo apt install python3.12 python3.12-venv
pip install poetry

# 2. Configure Poetry for in-project environments
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# 3. Setup project environment
poetry env use python3.12
poetry install --with dev --extras "tests retrieval chromadb api"
```

**Windows**:
```bash
# 1. Install Python 3.12 from python.org
# 2. Install Poetry via pip or chocolatey
pip install poetry

# 3. Configure Poetry
poetry config virtualenvs.create true
poetry config virtualenvs.in-project true

# 4. Setup environment (note: some extras may not be available on Windows)
poetry install --with dev --extras "tests api"
```

#### Development Tools Integration
- **Pre-commit Hooks**: `poetry run pre-commit install` for automatic code quality checks
- **Type Checking**: `poetry run mypy src/` for static type analysis
- **Code Formatting**: `poetry run black . && poetry run isort .` for consistent formatting
- **Testing**: `poetry run devsynth run-tests --speed=fast` for quick feedback

#### Troubleshooting Common Issues

**Problem**: Cursor rules not applying
**Solution**:
```bash
# Verify Cursor integration
poetry run python scripts/verify_cursor_integration.py

# Check rule files have proper YAML frontmatter
find .cursor/rules -name "*.mdc" -exec grep -l "alwaysApply:" {} \;
```

**Problem**: Poetry environment issues
**Solution**:
```bash
# Recreate environment
poetry env remove --all
poetry env use python3.12
poetry install --with dev --extras "tests retrieval chromadb api"

# Verify environment
poetry run python --version  # Should show 3.12.x from .venv
poetry run which python     # Should show .venv/bin/python
```

**Problem**: Tests failing in Cursor
**Solution**:
```bash
# Run tests within Poetry environment
poetry run devsynth run-tests --speed=fast --no-parallel

# Check for missing environment variables
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_OPENAI_AVAILABLE=true
```

#### Best Practices for Cursor + DevSynth

1. **Always Use Poetry Environment**: Never run Python commands directly - always use `poetry run`
2. **Follow EDRR Process**: Use Cursor commands for systematic development approach
3. **Specification First**: Check specifications before implementing any feature
4. **Test-Driven Development**: Write failing tests before implementation
5. **Quality Gates**: Run validation scripts before committing
6. **Platform Consistency**: Ensure consistent environment setup across team

### Reference Integration
- **Specifications**: Always check `docs/specifications/` for detailed requirements
- **Constitution**: Reference `constitution.md` for project-wide rules
- **BDD Tests**: Use `tests/behavior/features/` for acceptance criteria
- **Examples**: Reference `examples/` for implementation patterns
- **Scripts**: Use `scripts/` directory for validation and automation tools

## AGENTS.md Compliance

**What is the scope of these instructions?**
They apply to the entire repository and follow the OpenAI Codex AGENTS.md spec (repo-wide scope; nested AGENTS files override). Update AGENTS files whenever workflows change.

**Cursor Integration Scope:**
The Cursor IDE integration extends these instructions to provide structured AI assistance within the Cursor development environment. All Cursor configurations are designed to enhance, not replace, the established DevSynth development workflows and quality standards.

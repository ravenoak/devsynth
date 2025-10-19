# Unified Test CLI Implementation

**Issue Type**: Feature Enhancement
**Priority**: Critical
**Effort**: Large
**Created**: 2025-01-17
**Status**: Open

## Problem Statement

The current testing ecosystem has 200+ scripts with inconsistent interfaces, overlapping functionality, and significant maintenance overhead. This creates confusion for developers and makes the testing infrastructure harder to maintain than the code it tests.

## Proposed Solution

Implement a unified `devsynth test` command that consolidates all testing functionality under a single, consistent interface.

## CLI Design

### Core Command Structure

```bash
devsynth test <subcommand> [options]
```

### Subcommands

#### `run` - Execute Tests
```bash
devsynth test run [options]

Options:
  --target=<unit|integration|behavior|all>  Test target (default: unit)
  --speed=<fast|medium|slow|all>           Speed category (default: fast)
  --parallel / --no-parallel               Enable/disable parallel execution
  --smoke                                  Smoke mode (minimal plugins)
  --segment                                Enable segmented execution
  --segment-size=N                         Tests per segment (default: 50)
  --maxfail=N                              Stop after N failures
  --markers=EXPR                           Additional marker expression
  --keyword=PATTERN                        Keyword filter
  --report                                 Generate HTML report
  --verbose                                Verbose output

Examples:
  devsynth test run                        # Fast unit tests
  devsynth test run --target=all --speed=all --report
  devsynth test run --target=integration --speed=medium --no-parallel
  devsynth test run --smoke --speed=fast --maxfail=1
```

#### `coverage` - Coverage Analysis
```bash
devsynth test coverage [options]

Options:
  --format=<html|xml|json|term>            Output format (default: term)
  --threshold=N                            Coverage threshold (default: 80)
  --quality-check                          Enable quality-focused analysis
  --report-dir=PATH                        Output directory (default: htmlcov)
  --exclude=PATTERN                        Exclude pattern
  --include=PATTERN                        Include pattern

Examples:
  devsynth test coverage                   # Terminal coverage report
  devsynth test coverage --format=html --threshold=85
  devsynth test coverage --quality-check  # Focus on meaningful coverage
```

#### `validate` - Test Validation
```bash
devsynth test validate [options]

Options:
  --markers                                Validate speed markers
  --requirements                           Check requirement traceability
  --organization                           Validate test organization
  --isolation                              Check isolation necessity
  --report                                 Generate validation report
  --fix                                    Auto-fix issues where possible

Examples:
  devsynth test validate --markers         # Check speed marker discipline
  devsynth test validate --isolation      # Analyze isolation requirements
  devsynth test validate --all --report   # Complete validation with report
```

#### `collect` - Test Collection
```bash
devsynth test collect [options]

Options:
  --target=<unit|integration|behavior|all>  Collection target
  --speed=<fast|medium|slow|all>           Speed category
  --format=<json|text>                     Output format
  --cache / --no-cache                     Use collection cache
  --refresh                                Refresh cache
  --output=FILE                            Output file

Examples:
  devsynth test collect --target=unit --speed=fast
  devsynth test collect --format=json --output=tests.json
  devsynth test collect --refresh          # Refresh collection cache
```

#### `analyze` - Test Analysis
```bash
devsynth test analyze [options]

Options:
  --dependencies                           Analyze test dependencies
  --performance                            Performance analysis
  --quality                                Quality metrics analysis
  --mutation                               Mutation testing analysis
  --flaky                                  Flaky test detection
  --output=FILE                            Output file

Examples:
  devsynth test analyze --dependencies     # Isolation optimization analysis
  devsynth test analyze --performance      # Performance bottleneck analysis
  devsynth test analyze --quality --mutation  # Comprehensive quality analysis
```

#### `mutate` - Mutation Testing
```bash
devsynth test mutate [options]

Options:
  --target=MODULE                          Target module for mutation
  --threshold=N                            Mutation score threshold (default: 70)
  --output=FILE                            Report output file
  --operators=LIST                         Mutation operators to use
  --exclude=PATTERN                        Exclude pattern

Examples:
  devsynth test mutate --target=devsynth.core
  devsynth test mutate --threshold=80 --output=mutation_report.json
```

#### `properties` - Property-Based Testing
```bash
devsynth test properties [options]

Options:
  --validate                               Validate property test coverage
  --generate                               Generate property tests
  --examples=N                             Number of examples (default: 100)
  --deadline=MS                            Deadline in milliseconds
  --output=FILE                            Output file

Examples:
  devsynth test properties --validate      # Check property test coverage
  devsynth test properties --generate --target=devsynth.algorithms
```

#### `performance` - Performance Testing
```bash
devsynth test performance [options]

Options:
  --benchmark                              Run benchmark tests
  --regression-check                       Check for performance regressions
  --baseline                               Capture performance baseline
  --threshold=PCT                          Regression threshold percentage
  --output=FILE                            Output file

Examples:
  devsynth test performance --benchmark
  devsynth test performance --regression-check --threshold=20
  devsynth test performance --baseline     # Capture new baseline
```

## Implementation Plan

### Phase 1: Core CLI Framework (Week 1)

Create the basic CLI structure:

```python
# src/devsynth/application/cli/commands/test_cmd.py
"""
Unified test command implementation.
"""

import typer
from typing import Optional, List
from enum import Enum

app = typer.Typer(help="DevSynth testing commands")

class TestTarget(str, Enum):
    unit = "unit"
    integration = "integration"
    behavior = "behavior"
    all = "all"

class SpeedCategory(str, Enum):
    fast = "fast"
    medium = "medium"
    slow = "slow"
    all = "all"

@app.command()
def run(
    target: TestTarget = TestTarget.unit,
    speed: List[SpeedCategory] = typer.Option([SpeedCategory.fast]),
    parallel: bool = typer.Option(True, "--parallel/--no-parallel"),
    smoke: bool = False,
    segment: bool = False,
    segment_size: int = 50,
    maxfail: Optional[int] = None,
    markers: Optional[str] = None,
    keyword: Optional[str] = None,
    report: bool = False,
    verbose: bool = False,
):
    """Run tests with specified options."""
    from devsynth.testing.run_tests import run_tests

    # Convert CLI options to run_tests parameters
    speed_categories = [s.value for s in speed] if speed else None

    success, output = run_tests(
        target=target.value,
        speed_categories=speed_categories,
        verbose=verbose,
        report=report,
        parallel=parallel,
        segment=segment,
        segment_size=segment_size,
        maxfail=maxfail,
        extra_marker=markers,
        keyword_filter=keyword,
    )

    typer.echo(output)
    if not success:
        raise typer.Exit(1)

@app.command()
def coverage(
    format: str = "term",
    threshold: int = 80,
    quality_check: bool = False,
    report_dir: str = "htmlcov",
):
    """Generate coverage reports."""
    from devsynth.testing.coverage_analysis import generate_coverage_report

    success = generate_coverage_report(
        format=format,
        threshold=threshold,
        quality_check=quality_check,
        output_dir=report_dir,
    )

    if not success:
        raise typer.Exit(1)

@app.command()
def validate(
    markers: bool = False,
    requirements: bool = False,
    organization: bool = False,
    isolation: bool = False,
    report: bool = False,
    fix: bool = False,
):
    """Validate test suite quality and organization."""
    from devsynth.testing.validation import run_validation

    success = run_validation(
        check_markers=markers,
        check_requirements=requirements,
        check_organization=organization,
        check_isolation=isolation,
        generate_report=report,
        auto_fix=fix,
    )

    if not success:
        raise typer.Exit(1)

# Additional subcommands...
```

### Phase 2: Core Functionality (Week 2)

Implement the underlying functionality:

```python
# src/devsynth/testing/coverage_analysis.py
"""
Enhanced coverage analysis with quality focus.
"""

def generate_coverage_report(
    format: str = "term",
    threshold: int = 80,
    quality_check: bool = False,
    output_dir: str = "htmlcov",
) -> bool:
    """Generate coverage report with quality analysis."""

    if quality_check:
        # Focus on meaningful coverage metrics
        return _generate_quality_coverage_report(threshold, output_dir)
    else:
        # Standard coverage report
        return _generate_standard_coverage_report(format, threshold, output_dir)

def _generate_quality_coverage_report(threshold: int, output_dir: str) -> bool:
    """Generate quality-focused coverage analysis."""

    # Analyze coverage patterns
    coverage_data = _load_coverage_data()

    # Identify low-value coverage (getters, setters, trivial methods)
    low_value_lines = _identify_low_value_coverage(coverage_data)

    # Calculate meaningful coverage percentage
    meaningful_coverage = _calculate_meaningful_coverage(coverage_data, low_value_lines)

    # Generate enhanced report
    report = _generate_enhanced_coverage_report(
        coverage_data, meaningful_coverage, low_value_lines
    )

    # Save report
    _save_coverage_report(report, output_dir)

    return meaningful_coverage >= threshold
```

### Phase 3: Advanced Features (Week 3-4)

Implement mutation testing, property testing, and performance analysis:

```python
# src/devsynth/testing/mutation_testing.py
"""
Mutation testing implementation.
"""

class MutationTester:
    """Mutation testing for validating test effectiveness."""

    def run_mutation_testing(
        self,
        target_modules: List[str],
        threshold: float = 70.0,
        output_file: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Run mutation testing on target modules."""

        results = {
            'total_mutations': 0,
            'caught_mutations': 0,
            'mutation_score': 0.0,
            'module_results': {},
        }

        for module in target_modules:
            module_result = self._test_module_mutations(module)
            results['module_results'][module] = module_result
            results['total_mutations'] += module_result['total_mutations']
            results['caught_mutations'] += module_result['caught_mutations']

        if results['total_mutations'] > 0:
            results['mutation_score'] = (
                results['caught_mutations'] / results['total_mutations']
            ) * 100

        if output_file:
            self._save_results(results, output_file)

        return results
```

### Phase 4: Script Migration (Week 5-6)

Create migration utilities and deprecation warnings:

```python
# scripts/migrate_to_unified_cli.py
"""
Migration utility to help transition from old scripts to unified CLI.
"""

SCRIPT_MIGRATIONS = {
    'run_tests.sh': 'devsynth test run',
    'run_unified_tests.py': 'devsynth test run --target=all',
    'run_coverage_tests.py': 'devsynth test coverage',
    'verify_test_markers.py': 'devsynth test validate --markers',
    'run_mutation_tests.py': 'devsynth test mutate',
}

def generate_migration_guide():
    """Generate migration guide for existing scripts."""

    guide = [
        "# Migration Guide: Old Scripts to Unified CLI",
        "",
        "This guide shows how to migrate from old testing scripts to the new unified CLI.",
        "",
    ]

    for old_script, new_command in SCRIPT_MIGRATIONS.items():
        guide.extend([
            f"## {old_script}",
            f"**Old**: `./{old_script} [args]`",
            f"**New**: `{new_command} [options]`",
            "",
        ])

    return "\n".join(guide)
```

## Migration Strategy

### Phase 1: Parallel Implementation (Week 1-2)
- Implement unified CLI alongside existing scripts
- No disruption to current workflows
- Early feedback and testing

### Phase 2: Soft Migration (Week 3-4)
- Add deprecation warnings to old scripts
- Update documentation to recommend new CLI
- Provide migration examples

### Phase 3: Hard Migration (Week 5-6)
- Update CI workflows to use new CLI
- Move old scripts to `scripts/deprecated/`
- Provide clear migration path

### Phase 4: Cleanup (Week 7-8)
- Remove deprecated scripts
- Complete documentation update
- Team training and adoption

## Testing Strategy

### Unit Tests
```python
def test_run_command_with_unit_target():
    """Test run command with unit target."""
    result = runner.invoke(app, ['run', '--target=unit', '--speed=fast'])
    assert result.exit_code == 0
    assert 'Running unit tests' in result.output

def test_coverage_command_with_threshold():
    """Test coverage command with custom threshold."""
    result = runner.invoke(app, ['coverage', '--threshold=85'])
    assert result.exit_code == 0 or 'below threshold' in result.output
```

### Integration Tests
```python
def test_complete_test_workflow():
    """Test complete testing workflow using unified CLI."""
    # Run tests
    result = runner.invoke(app, ['run', '--target=unit', '--report'])
    assert result.exit_code == 0

    # Check coverage
    result = runner.invoke(app, ['coverage', '--format=html'])
    assert result.exit_code == 0

    # Validate tests
    result = runner.invoke(app, ['validate', '--markers'])
    assert result.exit_code == 0
```

## Documentation Plan

### User Documentation
- [ ] Command reference documentation
- [ ] Migration guide from old scripts
- [ ] Usage examples and tutorials
- [ ] Troubleshooting guide

### Developer Documentation
- [ ] CLI architecture documentation
- [ ] Extension points for new commands
- [ ] Testing patterns and conventions
- [ ] Performance optimization guide

## Success Metrics

### Quantitative
- **Script Reduction**: From 200+ to <50 scripts
- **Interface Consistency**: 100% of test operations through unified CLI
- **Migration Completion**: 0 deprecated scripts in active use
- **Developer Adoption**: >90% of team using unified CLI

### Qualitative
- **Developer Experience**: Faster onboarding, less confusion
- **Maintenance Burden**: Reduced time spent on script maintenance
- **Documentation Quality**: Clear, comprehensive testing guide
- **System Understanding**: Better insight into testing capabilities

## Dependencies

- [ ] Team approval for major CLI changes
- [ ] Coordination with CI/CD pipeline updates
- [ ] Documentation team collaboration
- [ ] Training resource allocation

## Related Issues

- [testing-infrastructure-consolidation.md](testing-infrastructure-consolidation.md)
- [testing-script-consolidation.md](testing-script-consolidation.md)

## References

- [Testing Principles](../docs/developer_guides/testing_principles.md)
- [CLI Command Patterns](../docs/developer_guides/cli_patterns.md)
- [Script Migration Guide](../docs/developer_guides/script_migration.md)

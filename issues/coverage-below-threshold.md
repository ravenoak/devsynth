# Coverage below threshold
Status: open

## Summary
Aggregated coverage runs complete but only produce 13.68 % line coverage (`test_reports/coverage.json`) and an empty `htmlcov/index.html`, so the ≥90 % gate remains unsatisfied even though the test command exits successfully.

## Steps to Reproduce
1. Ensure dependencies installed via `poetry install --with dev --all-extras`.
2. Execute the coverage command above.
3. Alternatively run `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report --maxfail=1` and inspect `test_reports/coverage.json`.

## Expected Behavior
Coverage report completes with ≥90% coverage.

## Actual Behavior
Coverage command exits successfully but reports only 13.68 % line coverage and produces empty HTML output, so the fail-under=90 guard is not satisfied.

## Next Actions
- [ ] Update `devsynth run-tests` to enforce coverage instrumentation for `src/devsynth` and regenerate htmlcov/coverage.json with ≥90 % results.
- [ ] Investigate why `.coverage` is missing after the 2025-09-16 smoke and aggregated runs despite passing `--cov`; ensure pytest-cov writes usable data before enforcement runs.
- [ ] Add targeted unit/integration tests for modules highlighted in docs/tasks.md §21 (output_formatter, webui, webui_bridge, logging_setup, reasoning_loop, testing/run_tests).
- [ ] Automate a coverage gate that inspects `test_reports/coverage.json` and fails when coverage <90 %.
- [ ] Resolve smoke profile coverage gap: either force-load pytest-cov when `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` or bypass enforcement when coverage is intentionally omitted (docs/tasks.md §21.8).

## Notes
- Tasks `docs/tasks.md` items 13.3 and 13.4 remain unchecked pending resolution.
- Address flake8 lint failures, as they may contribute to test instability.
- 2025-09-11: `poetry run pytest -q --cov-fail-under=90 -k "nonexistent_to_force_no_tests"` fails during test collection due to missing modules `faiss` and `chromadb`; coverage remains unverified.
- 2025-09-19: `devsynth` installed; smoke and property tests pass. Full coverage run not executed this iteration; threshold remains unverified.
- 2025-09-27: Segmented coverage run executed for fast and medium tests, combined via `coverage combine`; HTML and JSON reports archived outside version control (`coverage-artifacts.tar.gz`). Threshold still unverified.
- 2025-09-28: Combined report `coverage report --fail-under=90` returned 5% total coverage, confirming the ≥90% requirement is unmet.
- 2025-09-30: `poetry run coverage report --fail-under=90` after smoke run reported "No data to report"; coverage instrumentation missing.
- 2025-10-01: After reinstalling dependencies, `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` completed but produced only "Tests completed successfully" without coverage data.
- 2025-09-15: `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report --maxfail=1` completed yet `test_reports/coverage.json` reported 13.68 % and `htmlcov/index.html` remained empty; issue reopened and coverage remediation tasks added to docs/tasks.md section 21.
- 2025-09-15: Smoke profile run (`poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1`) emitted "Unable to determine total coverage…" and produced `{}` for `test_reports/coverage.json` after reinstalling the CLI via `poetry install --with dev --all-extras`; indicates pytest-cov is skipped when plugin autoload is disabled.
- 2025-09-16: `poetry run devsynth run-tests --smoke --speed=fast --no-parallel --maxfail=1` and `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report --maxfail=1` both succeeded yet printed "Unable to determine total coverage" and left `.coverage` absent; restoring `test_reports/coverage.json` from git shows the last known 13.68 % measurement persists until instrumentation is repaired.【63011a†L1-L4】【50195f†L1-L5】
- 2025-09-16: Documented formatter expectations in [docs/implementation/output_formatter_invariants.md](../docs/implementation/output_formatter_invariants.md) to guide new targeted tests.
- 2025-09-12: Coverage rerun via `poetry run devsynth run-tests --speed=fast --speed=medium --no-parallel --report` achieved 95% aggregate coverage; badge and documentation updated. Issue remains closed.
- 2025-10-07: Added targeted unit tests for provider system, WebUI, output formatter, WebUI bridge, logging, reasoning loop, and test runner; coverage remains below 90%.

## Coverage Gap Analysis

Recent exploratory run with `pytest --cov=src/devsynth --cov-report=term-missing --continue-on-collection-errors` produced a valid report showing an aggregate 20 % coverage across `src/devsynth` (38 918 statements, 31 100 missed)【50587d†L1】. The table below highlights representative files requiring substantial attention:

| Module | Stmts | Cover | Additional lines to reach 90 % | Key missing regions |
| --- | --- | --- | --- | --- |
| `adapters/provider_system.py` | 675 | 12 % | ≈526 | `55`, `60‑85`, `90`, `106‑151`, `178‑321`, `335‑350`, `354‑361`, `378`, `466‑467`, `496‑497`, `503‑509`, `520‑521`, `532`, `541‑545`, `548`, `570‑591`, `595‑600`, `604`, `640‑710`, `720‑827`, `837‑843`, `864‑910`, `914‑995`, `1015‑1044`, `1051‑1056`, `1060`, `1096‑1171`, `1183‑1295`, `1305‑1311`, `1332‑1378`, `1384‑1460`, `1474‑1493`, `1500‑1523`, `1527`, `1530‑1538`, `1543‑1571`, `1583‑1606`, `1620‑1643`, `1649‑1666`, `1672‑1689`, `1708‑1711`, `1738‑1751`, `1770‑1779`, `1796‑1798`, `1812‑1821`【168681†L1-L3】 |
| `interface/webui.py` | 1053 | 10 % | ≈839 | `51‑59`, `64‑65`, `119‑123`, `202‑227`, `254‑318`, `331‑336`, `339`, `351‑446`, `458`, `469‑494`, `566`, `577‑627`, `631‑644`, `648‑701`, `711‑731`, `735‑744`, `757‑777`, `781‑794`, `806‑815`, `823‑834`, `840`, `847‑869`, `873‑985`, `989‑999`, `1005‑1029`, `1052‑1090`, `1107‑1248`, `1253‑1384`, `1391‑1392`, `1397‑1414`, `1419‑1429`, `1434‑1505`, `1518‑1556`, `1560‑1594`, `1603‑1659`, `1667‑1749`, `1757‑1813`, `1817‑1835`, `1839‑1866`, `1870‑1895`, `1899‑1922`, `1926‑1951`, `1955‑1977`, `1981‑2004`, `2008‑2033`, `2037‑2062`, `2066‑2079`, `2083‑2103`, `2107‑2121`, `2125‑2145`, `2149‑2162`, `2166‑2191`, `2198‑2373`, `2378`【66a050†L1-L3】 |
| `interface/output_formatter.py` | 258 | 22 % | ≈176 | `110‑120`, `131‑148`, `164‑198`, `207‑221`, `229`, `241‑254`, `269‑279`, `294‑354`, `368‑399`, `411‑427`, `441‑456`, `470‑496`, `509‑512`, `527‑541`, `553‑558`, `577‑584`【7d791d†L1-L2】 |
| `interface/webui_bridge.py` | 205 | 19 % | ≈147 | `29`, `45‑50`, `67‑99`, `103`, `116‑130`, `142‑154`, `162‑171`, `191‑216`, `235‑294`, `303‑314`, `325‑326`, `350‑371`, `390‑423`, `447‑450`, `465‑468`, `474‑500`, `514`, `534`, `551`【aaa475†L1-L2】 |
| `logging_setup.py` | 243 | 38 % | ≈126 | `68`, `72‑76`, `80`, `83‑84`, `88‑94`, `108‑113`, `123‑180`, `198‑201`, `206‑207`, `217‑219`, `229‑232`, `255‑304`, `328‑457`, `498‑503`, `531`, `534‑538`, `542`, `544`, `546`, `548`, `566`, `570`, `574‑575`【d6b265†L1-L4】 |
| `methodology/edrr/reasoning_loop.py` | 79 | 14 % | ≈61 | `24`, `54‑178`【fc6bba†L1-L2】 |
| `testing/run_tests.py` | 277 | 7 % | ≈230 | `29‑31`, `39‑71`, `92‑102`, `123‑327`, `364‑619`【95c072†L1-L2】 |
| `ports/requirement_port.py` | 114 | 70 % | ≈23 | `33`, `43`, `56`, `69`, `82`, `95`, `112`, `127`, `140`, `153`, `170`, `185`, `198`, `215`, `230`, `243`, `260`, `273`, `286`, `299`, `312`, `332`, `349`, `365`, `381`, `395`, `405`, `415`, `425`, `444`, `460`, `473`, `486`, `499`【1746f7†L1-L3】 |

## Dialectical Examination

- **Thesis:** Raising coverage above 90 % yields higher confidence in system behavior and eases regression detection.
- **Antithesis:** Pursuing coverage mechanically may overlook critical paths or encourage brittle tests.
- **Synthesis:** Combine quantitative targets with qualitative review—prioritize meaningful scenarios, refactor for testability, and retire obsolete code.

## Socratic Action Plan

1. **Question:** *Which behaviors are untested in the largest modules?*
   **Answer:** The regions listed above show unexercised branches; each deserves targeted unit or integration tests.
2. **Question:** *What dependencies block execution?*
   **Answer:** Missing optional packages (`faiss`, `chromadb`) halted collection; installing dev extras or guarding imports enables broader test execution.
3. **Question:** *How can cross-discipline practices help?*
   **Answer:** Pair TDD with static analysis and design reviews, leveraging QA expertise to craft acceptance criteria that map to the uncovered lines.
4. **Question:** *What proves success?*
   **Answer:** A rerun of the coverage command with `--fail-under=90` passing, coupled with peer-reviewed test cases covering the highlighted regions.

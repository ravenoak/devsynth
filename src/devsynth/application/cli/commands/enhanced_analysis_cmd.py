"""
Enhanced Analysis Command

This module provides a comprehensive command that runs all enhanced analysis
capabilities including test infrastructure analysis, quality assurance,
security validation, and requirements traceability.

Key features:
- Unified command interface for all enhanced analysis tools
- Configurable analysis scope and depth
- Integration with DevSynth's EDRR workflow system
- Comprehensive reporting with multiple output formats
- Memory system integration for persistent analysis results
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from devsynth.application.quality.dialectical_audit_system import DialecticalAuditSystem
from devsynth.application.quality.requirements_traceability_engine import (
    RequirementsTraceabilityEngine,
)
from devsynth.application.security.security_audit_system import SecurityAuditSystem
from devsynth.application.testing.enhanced_test_collector import EnhancedTestCollector
from devsynth.application.testing.test_isolation_analyzer import TestIsolationAnalyzer
from devsynth.application.testing.test_report_generator import TestReportGenerator
from devsynth.ports.memory_port import MemoryPort


class EnhancedAnalysisCommand:
    """
    Command for running comprehensive enhanced analysis.

    This command provides a unified interface to run all enhanced analysis
    capabilities including test infrastructure analysis, quality assurance,
    security validation, and requirements traceability.
    """

    def __init__(self):
        """Initialize the enhanced analysis command."""
        self.console = Console()
        self.memory_port = None  # Will be initialized when needed

    def run_enhanced_analysis(
        self,
        project_path: str = ".",
        include_tests: bool = True,
        include_quality: bool = True,
        include_security: bool = True,
        include_traceability: bool = True,
        output_format: str = "console",
        output_file: str | None = None,
        verbose: bool = False,
        dry_run: bool = False,
    ) -> int:
        """
        Run comprehensive enhanced analysis.

        Args:
            project_path: Path to the project to analyze
            include_tests: Whether to include test infrastructure analysis
            include_quality: Whether to include quality assurance analysis
            include_security: Whether to include security validation
            include_traceability: Whether to include requirements traceability
            output_format: Output format (console, json, html, markdown)
            output_file: Optional output file path
            verbose: Whether to show detailed progress
            dry_run: Whether to run in dry-run mode

        Returns:
            Exit code (0 for success, non-zero for errors)
        """
        if dry_run:
            self.console.print(
                "[yellow]DRY RUN: Enhanced analysis would be performed[/yellow]"
            )
            return 0

        start_time = time.time()

        # Initialize memory port if available
        try:
            from devsynth.memory.sync_manager import MemorySyncManager

            self.memory_port = MemorySyncManager.get_default_port()
        except Exception:
            self.memory_port = None

        # Initialize analysis components
        analysis_results = {}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:

            # Test Infrastructure Analysis
            if include_tests:
                progress.add_task("Analyzing test infrastructure...", total=None)
                test_results = self._analyze_test_infrastructure(project_path, verbose)
                analysis_results["test_infrastructure"] = test_results

            # Quality Assurance Analysis
            if include_quality:
                progress.add_task("Running quality assurance analysis...", total=None)
                quality_results = self._analyze_quality_assurance(project_path, verbose)
                analysis_results["quality_assurance"] = quality_results

            # Security Validation
            if include_security:
                progress.add_task("Performing security validation...", total=None)
                security_results = self._analyze_security(project_path, verbose)
                analysis_results["security"] = security_results

            # Requirements Traceability
            if include_traceability:
                progress.add_task("Verifying requirements traceability...", total=None)
                traceability_results = self._analyze_traceability(project_path, verbose)
                analysis_results["traceability"] = traceability_results

        # Generate comprehensive report
        total_time = time.time() - start_time

        if output_format == "console":
            self._display_console_report(analysis_results, total_time)
        elif output_format == "json":
            self._generate_json_report(analysis_results, total_time, output_file)
        elif output_format == "html":
            self._generate_html_report(analysis_results, total_time, output_file)
        elif output_format == "markdown":
            self._generate_markdown_report(analysis_results, total_time, output_file)

        # Store results in memory if available
        if self.memory_port:
            self._store_analysis_results(analysis_results, total_time)

        return 0

    def _analyze_test_infrastructure(
        self, project_path: str, verbose: bool
    ) -> dict[str, Any]:
        """Analyze test infrastructure."""
        results = {"status": "completed", "timestamp": time.time(), "components": {}}

        try:
            # Initialize test infrastructure components
            test_collector = EnhancedTestCollector(self.memory_port)
            isolation_analyzer = TestIsolationAnalyzer()
            report_generator = TestReportGenerator()

            # Collect tests
            test_collection = test_collector.collect_tests()
            results["components"]["test_collection"] = {
                "status": "success",
                "total_tests": sum(len(tests) for tests in test_collection.values()),
                "categories": {
                    cat: len(tests) for cat, tests in test_collection.items()
                },
            }

            # Analyze isolation
            isolation_report = isolation_analyzer.analyze_test_isolation("tests")
            results["components"]["isolation_analysis"] = {
                "status": "success",
                "total_issues": isolation_report.total_issues,
                "issues_by_severity": isolation_report.issues_by_severity,
                "issues_by_type": isolation_report.issues_by_type,
            }

            # Generate report
            report = report_generator.generate_comprehensive_report(
                test_collection, isolation_report
            )
            results["components"]["report_generation"] = {
                "status": "success",
                "report_generated": True,
            }

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            if verbose:
                self.console.print(
                    f"[red]Test infrastructure analysis failed: {e}[/red]"
                )

        return results

    def _analyze_quality_assurance(
        self, project_path: str, verbose: bool
    ) -> dict[str, Any]:
        """Analyze quality assurance."""
        results = {"status": "completed", "timestamp": time.time(), "components": {}}

        try:
            # Initialize quality assurance components
            audit_system = DialecticalAuditSystem(self.memory_port)
            traceability_engine = RequirementsTraceabilityEngine()

            # Run dialectical audit
            audit_result = audit_system.run_dialectical_audit(project_path)
            results["components"]["dialectical_audit"] = {
                "status": "success",
                "total_features": audit_result.total_features_found,
                "inconsistencies": audit_result.inconsistencies_found,
                "questions_generated": len(audit_result.questions_generated),
            }

            # Analyze traceability gaps
            gaps = traceability_engine.analyze_traceability_gaps(Path(project_path))
            results["components"]["traceability_analysis"] = {
                "status": "success",
                "gaps_found": len(gaps),
                "gap_types": list({gap.gap_type for gap in gaps}),
            }

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            if verbose:
                self.console.print(f"[red]Quality assurance analysis failed: {e}[/red]")

        return results

    def _analyze_security(self, project_path: str, verbose: bool) -> dict[str, Any]:
        """Analyze security."""
        results = {"status": "completed", "timestamp": time.time(), "components": {}}

        try:
            # Initialize security components
            security_audit = SecurityAuditSystem(self.memory_port)

            # Run comprehensive security audit
            audit_report = security_audit.generate_comprehensive_report(project_path)
            results["components"]["security_audit"] = {
                "status": "success",
                "overall_score": audit_report.overall_score,
                "risk_level": audit_report.risk_level,
                "total_issues": (
                    (
                        audit_report.bandit_report.total_issues
                        if audit_report.bandit_report
                        else 0
                    )
                    + (
                        audit_report.safety_report.total_vulnerabilities
                        if audit_report.safety_report
                        else 0
                    )
                    + (
                        audit_report.custom_report.issues_found
                        if audit_report.custom_report
                        else 0
                    )
                ),
            }

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            if verbose:
                self.console.print(f"[red]Security analysis failed: {e}[/red]")

        return results

    def _analyze_traceability(self, project_path: str, verbose: bool) -> dict[str, Any]:
        """Analyze requirements traceability."""
        results = {"status": "completed", "timestamp": time.time(), "components": {}}

        try:
            # Initialize traceability components
            traceability_engine = RequirementsTraceabilityEngine()

            # Analyze traceability gaps
            gaps = traceability_engine.analyze_traceability_gaps(Path(project_path))
            results["components"]["gap_analysis"] = {
                "status": "success",
                "gaps_found": len(gaps),
                "gap_types": list({gap.gap_type for gap in gaps}),
            }

            # Generate traceability matrix
            matrix = traceability_engine.generate_traceability_matrix(
                Path(project_path)
            )
            results["components"]["matrix_generation"] = {
                "status": "success",
                "matrix_generated": True,
            }

        except Exception as e:
            results["status"] = "failed"
            results["error"] = str(e)
            if verbose:
                self.console.print(f"[red]Traceability analysis failed: {e}[/red]")

        return results

    def _display_console_report(
        self, analysis_results: dict[str, Any], total_time: float
    ) -> None:
        """Display analysis results in console format."""
        self.console.print("\n[bold blue]🔍 ENHANCED ANALYSIS REPORT[/bold blue]")
        self.console.print(f"[dim]Completed in {total_time:.1f}[/dim]\n")

        # Overall status
        failed_components = [
            k for k, v in analysis_results.items() if v.get("status") == "failed"
        ]
        if failed_components:
            self.console.print(
                f"[red]❌ Some components failed: {', '.join(failed_components)}[/red]"
            )

        # Analysis components
        for component_name, component_results in analysis_results.items():
            status = component_results.get("status", "unknown")
            status_icon = "✅" if status == "completed" else "❌"

            self.console.print(
                f"\n[bold]{component_name.replace('_', ' ').title()}[/bold]"
            )
            self.console.print(f"{status_icon} Status: {status}")

            if "components" in component_results:
                for comp_name, comp_data in component_results["components"].items():
                    comp_status = comp_data.get("status", "unknown")
                    comp_icon = "✅" if comp_status == "success" else "❌"
                    self.console.print(
                        f"  {comp_icon} {comp_name.replace('_', ' ').title()}"
                    )

                    # Show key metrics
                    if "total_tests" in comp_data:
                        self.console.print(f"    📊 Tests: {comp_data['total_tests']}")
                    if "total_issues" in comp_data:
                        self.console.print(
                            f"    🔍 Issues: {comp_data['total_issues']}"
                        )
                    if "overall_score" in comp_data:
                        self.console.print(
                            f"    🛡️ Score: {comp_data['overall_score']:.1f}"
                        )
                    if "gaps_found" in comp_data:
                        self.console.print(f"    🔗 Gaps: {comp_data['gaps_found']}")

        self.console.print(
            "\n[dim]Use --output-format json/html/markdown for detailed reports[/dim]"
        )

    def _generate_json_report(
        self,
        analysis_results: dict[str, Any],
        total_time: float,
        output_file: str | None,
    ) -> None:
        """Generate JSON report."""
        report_data = {
            "timestamp": time.time(),
            "total_time": total_time,
            "analysis_results": analysis_results,
        }

        if output_file:
            with open(output_file, "w") as f:
                json.dump(report_data, f, indent=2, default=str)
            self.console.print(f"[green]JSON report saved to: {output_file}[/green]")
        else:
            self.console.print_json(data=report_data)

    def _generate_html_report(
        self,
        analysis_results: dict[str, Any],
        total_time: float,
        output_file: str | None,
    ) -> None:
        """Generate HTML report."""
        # Generate comprehensive HTML report
        html_content = self._create_html_report(analysis_results, total_time)

        if output_file:
            with open(output_file, "w") as f:
                f.write(html_content)
            self.console.print(f"[green]HTML report saved to: {output_file}[/green]")
        else:
            self.console.print(html_content)

    def _generate_markdown_report(
        self,
        analysis_results: dict[str, Any],
        total_time: float,
        output_file: str | None,
    ) -> None:
        """Generate Markdown report."""
        # Generate comprehensive Markdown report
        markdown_content = self._create_markdown_report(analysis_results, total_time)

        if output_file:
            with open(output_file, "w") as f:
                f.write(markdown_content)
            self.console.print(
                f"[green]Markdown report saved to: {output_file}[/green]"
            )
        else:
            self.console.print(markdown_content)

    def _create_html_report(
        self, analysis_results: dict[str, Any], total_time: float
    ) -> str:
        """Create HTML report content."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevSynth Enhanced Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; }}
                .component {{ background: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .success {{ color: green; }}
                .error {{ color: red; }}
                .metric {{ background: #f1f3f4; padding: 8px; margin: 5px 0; border-radius: 3px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DevSynth Enhanced Analysis Report</h1>
                <p><strong>Generated:</strong> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p><strong>Total Time:</strong> {total_time:.1f} seconds</p>
            </div>
        """

        for component_name, component_results in analysis_results.items():
            status = component_results.get("status", "unknown")
            status_class = "success" if status == "completed" else "error"

            html += f"""
            <div class="section">
                <h2>{component_name.replace('_', ' ').title()}</h2>
                <div class="component">
                    <p><strong>Status:</strong> <span class="{status_class}">{status}</span></p>
            """

            if "components" in component_results:
                html += "<h3>Components:</h3>"
                for comp_name, comp_data in component_results["components"].items():
                    comp_status = comp_data.get("status", "unknown")
                    comp_class = "success" if comp_status == "success" else "error"

                    html += f"""
                    <div class="metric">
                        <strong>{comp_name.replace('_', ' ').title()}:</strong>
                        <span class="{comp_class}">{comp_status}</span>
                    """

                    # Add key metrics
                    if "total_tests" in comp_data:
                        html += f"<br><span>Tests: {comp_data['total_tests']}</span>"
                    if "total_issues" in comp_data:
                        html += f"<br><span>Issues: {comp_data['total_issues']}</span>"
                    if "overall_score" in comp_data:
                        html += (
                            f"<br><span>Score: {comp_data['overall_score']:.1f}</span>"
                        )
                    if "gaps_found" in comp_data:
                        html += f"<br><span>Gaps: {comp_data['gaps_found']}</span>"

                    html += "</div>"

            html += "</div></div>"

        html += """
        </body>
        </html>
        """

        return html

    def _create_markdown_report(
        self, analysis_results: dict[str, Any], total_time: float
    ) -> str:
        """Create Markdown report content."""
        markdown = f"""# DevSynth Enhanced Analysis Report

**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')}
**Total Time:** {total_time:.1f} seconds

"""

        for component_name, component_results in analysis_results.items():
            status = component_results.get("status", "unknown")
            status_icon = "✅" if status == "completed" else "❌"

            markdown += f"## {component_name.replace('_', ' ').title()}\n\n"
            markdown += f"- **Status:** {status_icon} {status}\n"

            if "components" in component_results:
                markdown += "\n### Components\n\n"
                for comp_name, comp_data in component_results["components"].items():
                    comp_status = comp_data.get("status", "unknown")
                    comp_icon = "✅" if comp_status == "success" else "❌"

                    markdown += f"- **{comp_name.replace('_', ' ').title()}:** {comp_icon} {comp_status}\n"

                    # Add key metrics
                    if "total_tests" in comp_data:
                        markdown += f"  - Tests: {comp_data['total_tests']}\n"
                    if "total_issues" in comp_data:
                        markdown += f"  - Issues: {comp_data['total_issues']}\n"
                    if "overall_score" in comp_data:
                        markdown += f"  - Score: {comp_data['overall_score']:.1f}\n"
                    if "gaps_found" in comp_data:
                        markdown += f"  - Gaps: {comp_data['gaps_found']}\n"

            markdown += "\n"

        return markdown

    def _store_analysis_results(
        self, analysis_results: dict[str, Any], total_time: float
    ) -> None:
        """Store analysis results in memory system."""
        if not self.memory_port:
            return

        try:
            memory_key = "enhanced_analysis_latest"
            self.memory_port.store(
                key=memory_key,
                data={
                    "timestamp": time.time(),
                    "total_time": total_time,
                    "components_analyzed": len(analysis_results),
                    "overall_status": all(
                        result.get("status") == "completed"
                        for result in analysis_results.values()
                    ),
                    "analysis_results": analysis_results,
                },
                metadata={"type": "enhanced_analysis", "version": "1.0"},
            )

        except Exception:
            # Memory storage failed, but don't fail the operation
            pass


def create_enhanced_analysis_command():
    """Create the enhanced analysis command."""
    command = EnhancedAnalysisCommand()

    @typer.run
    def enhanced_analysis(
        project_path: str = typer.Option(".", help="Path to the project to analyze"),
        include_tests: bool = typer.Option(
            True, help="Include test infrastructure analysis"
        ),
        include_quality: bool = typer.Option(
            True, help="Include quality assurance analysis"
        ),
        include_security: bool = typer.Option(True, help="Include security validation"),
        include_traceability: bool = typer.Option(
            True, help="Include requirements traceability"
        ),
        output_format: str = typer.Option(
            "console", help="Output format (console, json, html, markdown)"
        ),
        output_file: str | None = typer.Option(None, help="Output file path"),
        verbose: bool = typer.Option(False, help="Show detailed progress"),
        dry_run: bool = typer.Option(False, help="Run in dry-run mode"),
    ):
        """Run comprehensive enhanced analysis on a DevSynth project."""
        return command.run_enhanced_analysis(
            project_path=project_path,
            include_tests=include_tests,
            include_quality=include_quality,
            include_security=include_security,
            include_traceability=include_traceability,
            output_format=output_format,
            output_file=output_file,
            verbose=verbose,
            dry_run=dry_run,
        )

    return enhanced_analysis

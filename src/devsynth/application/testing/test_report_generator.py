"""
Test Report Generator

This module generates comprehensive reports for test infrastructure analysis,
providing detailed insights into test coverage, quality metrics, and improvement
opportunities across different formats (HTML, JSON, Markdown).

Key features:
- Comprehensive test reporting with multiple output formats
- Test count analysis by category and markers
- Isolation issue reporting with severity breakdown
- Quality metrics and improvement suggestions
- Integration with DevSynth's memory system for persistent reporting
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from devsynth.application.testing.enhanced_test_collector import TestCollectionResult, IsolationReport


@dataclass
class TestReport:
    """Comprehensive test infrastructure report."""
    timestamp: datetime
    project_path: str
    total_tests: int
    test_counts: Dict[str, int]
    marker_distribution: Dict[str, int]
    isolation_issues: Dict[str, int]
    quality_metrics: Dict[str, float]
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    report_format: str


@dataclass
class QualityMetrics:
    """Test quality metrics."""
    organization_score: float
    isolation_score: float
    coverage_score: float
    maintainability_score: float
    overall_score: float


@dataclass
class PerformanceMetrics:
    """Test performance metrics."""
    collection_time: float
    analysis_time: float
    enhancement_time: float
    report_generation_time: float
    average_test_execution_time: float


class TestReportGenerator:
    """
    Generates comprehensive test reports from analysis results.

    This class creates detailed reports about test infrastructure including:
    - Test counts and distribution by category and markers
    - Isolation analysis results with severity breakdown
    - Quality metrics and improvement suggestions
    - Performance metrics and optimization recommendations
    - Multiple output formats (HTML, JSON, Markdown)
    """

    def __init__(self):
        """Initialize the test report generator."""
        self.templates_dir = Path(__file__).parent / "templates"
        self.output_dir = Path.cwd() / "test_reports"
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self,
        collection_results: Dict[str, Any],
        isolation_report: Optional[IsolationReport] = None,
        quality_metrics: Optional[QualityMetrics] = None,
        performance_metrics: Optional[PerformanceMetrics] = None,
        output_format: str = "html",
        output_file: Optional[str] = None
    ) -> str:
        """
        Generate comprehensive test report.

        Args:
            collection_results: Results from test collection
            isolation_report: Results from isolation analysis
            quality_metrics: Quality metrics for the test suite
            performance_metrics: Performance metrics for test operations
            output_format: Output format (html, json, markdown)
            output_file: Optional output file path

        Returns:
            Generated report content
        """
        # Compile report data
        report_data = self._compile_report_data(
            collection_results,
            isolation_report,
            quality_metrics,
            performance_metrics
        )

        # Generate report in specified format
        if output_format.lower() == "html":
            report_content = self._generate_html_report(report_data)
        elif output_format.lower() == "json":
            report_content = self._generate_json_report(report_data)
        elif output_format.lower() == "markdown":
            report_content = self._generate_markdown_report(report_data)
        else:
            raise ValueError(f"Unsupported format: {output_format}")

        # Save to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report_content, encoding="utf-8")

        return report_content

    def generate_test_count_report(
        self,
        collection_results: Dict[str, Any],
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate test count analysis report.

        Args:
            collection_results: Results from test collection
            output_format: Output format

        Returns:
            Test count report data
        """
        total_tests = sum(len(tests) for tests in collection_results.values())

        # Count tests by category
        category_counts = {}
        for category, tests in collection_results.items():
            category_counts[category] = len(tests)

        # Analyze markers (simplified version)
        marker_counts = {"fast": 0, "medium": 0, "slow": 0}
        for tests in collection_results.values():
            for test_file in tests:
                for marker in marker_counts:
                    if f"@{marker}" in test_file or f"pytest.mark.{marker}" in test_file:
                        marker_counts[marker] += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": total_tests,
            "category_breakdown": category_counts,
            "marker_distribution": marker_counts,
            "categories": list(collection_results.keys()),
            "analysis_time": time.time()
        }

    def generate_marker_detection_report(
        self,
        test_files: List[str],
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate test marker detection report.

        Args:
            test_files: List of test files to analyze
            output_format: Output format

        Returns:
            Marker detection report data
        """
        marker_counts = {"fast": 0, "medium": 0, "slow": 0, "unmarked": 0}

        for test_file in test_files:
            marked = False
            for marker in ["fast", "medium", "slow"]:
                if self._test_has_marker(test_file, marker):
                    marker_counts[marker] += 1
                    marked = True

            if not marked:
                marker_counts["unmarked"] += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": len(test_files),
            "marker_counts": marker_counts,
            "marker_coverage": (len(test_files) - marker_counts["unmarked"]) / len(test_files) * 100,
            "missing_markers": marker_counts["unmarked"]
        }

    def generate_test_isolation_report(
        self,
        isolation_report: IsolationReport,
        output_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Generate test isolation analysis report.

        Args:
            isolation_report: Results from isolation analysis
            output_format: Output format

        Returns:
            Isolation report data
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "total_issues": isolation_report.total_issues,
            "issues_by_severity": isolation_report.issues_by_severity,
            "issues_by_type": isolation_report.issues_by_type,
            "files_analyzed": isolation_report.files_analyzed,
            "analysis_time": isolation_report.analysis_time,
            "severity_percentages": self._calculate_severity_percentages(isolation_report),
            "recommendations": self._generate_isolation_recommendations(isolation_report)
        }

    def _compile_report_data(
        self,
        collection_results: Dict[str, Any],
        isolation_report: Optional[IsolationReport],
        quality_metrics: Optional[QualityMetrics],
        performance_metrics: Optional[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """Compile all report data into a unified structure."""
        # Calculate basic metrics
        total_tests = sum(len(tests) for tests in collection_results.values())
        category_counts = {cat: len(tests) for cat, tests in collection_results.items()}

        # Marker analysis
        marker_counts = {"fast": 0, "medium": 0, "slow": 0}
        for tests in collection_results.values():
            for test_file in tests:
                for marker in marker_counts:
                    if self._test_has_marker(test_file, marker):
                        marker_counts[marker] += 1

        # Isolation analysis
        isolation_data = {}
        if isolation_report:
            isolation_data = {
                "total_issues": isolation_report.total_issues,
                "issues_by_severity": isolation_report.issues_by_severity,
                "issues_by_type": isolation_report.issues_by_type,
                "severity_percentages": self._calculate_severity_percentages(isolation_report)
            }

        # Quality metrics
        quality_data = {}
        if quality_metrics:
            quality_data = asdict(quality_metrics)

        # Performance metrics
        performance_data = {}
        if performance_metrics:
            performance_data = asdict(performance_metrics)

        # Generate recommendations
        recommendations = self._generate_comprehensive_recommendations(
            collection_results,
            isolation_report,
            quality_metrics,
            performance_metrics
        )

        return {
            "timestamp": datetime.now(),
            "project_path": str(Path.cwd()),
            "total_tests": total_tests,
            "test_counts": category_counts,
            "marker_distribution": marker_counts,
            "isolation_issues": isolation_data,
            "quality_metrics": quality_data,
            "performance_metrics": performance_data,
            "recommendations": recommendations
        }

    def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevSynth Test Infrastructure Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { background: #f8f9fa; padding: 20px; border-radius: 5px; }
                .section { margin: 20px 0; }
                .metric { background: #e9ecef; padding: 10px; margin: 5px 0; border-radius: 3px; }
                .recommendation { background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }
                .issue { background: #f8d7da; padding: 10px; margin: 5px 0; border-radius: 3px; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DevSynth Test Infrastructure Report</h1>
                <p>Generated: {timestamp}</p>
                <p>Project: {project_path}</p>
            </div>

            <div class="section">
                <h2>Test Overview</h2>
                <div class="metric">
                    <strong>Total Tests:</strong> {total_tests}
                </div>
                <table>
                    <tr><th>Category</th><th>Count</th></tr>
                    {category_rows}
                </table>
            </div>

            <div class="section">
                <h2>Marker Distribution</h2>
                <table>
                    <tr><th>Marker</th><th>Count</th></tr>
                    {marker_rows}
                </table>
            </div>

            {isolation_section}

            {quality_section}

            {performance_section}

            <div class="section">
                <h2>Recommendations</h2>
                {recommendations}
            </div>
        </body>
        </html>
        """

        # Format category rows
        category_rows = "\n".join(
            f'<tr><td>{cat}</td><td>{count}</td></tr>'
            for cat, count in report_data["test_counts"].items()
        )

        # Format marker rows
        marker_rows = "\n".join(
            f'<tr><td>{marker}</td><td>{count}</td></tr>'
            for marker, count in report_data["marker_distribution"].items()
        )

        # Format isolation section
        isolation_section = ""
        if "isolation_issues" in report_data and report_data["isolation_issues"]:
            isolation = report_data["isolation_issues"]
            isolation_section = f"""
            <div class="section">
                <h2>Isolation Analysis</h2>
                <div class="metric">
                    <strong>Total Issues:</strong> {isolation["total_issues"]}
                </div>
                <table>
                    <tr><th>Severity</th><th>Count</th></tr>
                    {self._format_severity_rows(isolation["issues_by_severity"])}
                </table>
            </div>
            """

        # Format quality section
        quality_section = ""
        if "quality_metrics" in report_data and report_data["quality_metrics"]:
            quality = report_data["quality_metrics"]
            quality_section = f"""
            <div class="section">
                <h2>Quality Metrics</h2>
                <div class="metric">
                    <strong>Overall Score:</strong> {quality.get("overall_score", "N/A")}
                </div>
                <table>
                    <tr><th>Metric</th><th>Score</th></tr>
                    {self._format_quality_rows(quality)}
                </table>
            </div>
            """

        # Format performance section
        performance_section = ""
        if "performance_metrics" in report_data and report_data["performance_metrics"]:
            perf = report_data["performance_metrics"]
            performance_section = f"""
            <div class="section">
                <h2>Performance Metrics</h2>
                <table>
                    <tr><th>Operation</th><th>Time (seconds)</th></tr>
                    {self._format_performance_rows(perf)}
                </table>
            </div>
            """

        # Format recommendations
        recommendations = "\n".join(
            f'<div class="recommendation">{rec}</div>'
            for rec in report_data["recommendations"]
        )

        return template.format(
            timestamp=report_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            project_path=report_data["project_path"],
            total_tests=report_data["total_tests"],
            category_rows=category_rows,
            marker_rows=marker_rows,
            isolation_section=isolation_section,
            quality_section=quality_section,
            performance_section=performance_section,
            recommendations=recommendations
        )

    def _generate_json_report(self, report_data: Dict[str, Any]) -> str:
        """Generate JSON report."""
        # Convert datetime to ISO format for JSON serialization
        json_data = self._prepare_for_json(report_data)
        return json.dumps(json_data, indent=2, default=str)

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        template = """# DevSynth Test Infrastructure Report

**Generated:** {timestamp}
**Project:** {project_path}

## Test Overview

**Total Tests:** {total_tests}

### Tests by Category

| Category | Count |
|----------|-------|
{category_table}

### Marker Distribution

| Marker | Count |
|--------|-------|
{marker_table}

{isolation_section}

{quality_section}

{performance_section}

## Recommendations

{recommendations}
"""

        # Format category table
        category_table = "\n".join(
            f"| {cat} | {count} |"
            for cat, count in report_data["test_counts"].items()
        )

        # Format marker table
        marker_table = "\n".join(
            f"| {marker} | {count} |"
            for marker, count in report_data["marker_distribution"].items()
        )

        # Format isolation section
        isolation_section = ""
        if "isolation_issues" in report_data and report_data["isolation_issues"]:
            isolation = report_data["isolation_issues"]
            isolation_section = f"""
## Isolation Analysis

**Total Issues:** {isolation["total_issues"]}

### Issues by Severity

| Severity | Count |
|----------|-------|
{self._format_severity_markdown(isolation["issues_by_severity"])}

"""

        # Format quality section
        quality_section = ""
        if "quality_metrics" in report_data and report_data["quality_metrics"]:
            quality = report_data["quality_metrics"]
            quality_section = f"""
## Quality Metrics

**Overall Score:** {quality.get("overall_score", "N/A")}

| Metric | Score |
|--------|-------|
{self._format_quality_markdown(quality)}

"""

        # Format performance section
        performance_section = ""
        if "performance_metrics" in report_data and report_data["performance_metrics"]:
            perf = report_data["performance_metrics"]
            performance_section = f"""
## Performance Metrics

| Operation | Time (seconds) |
|-----------|----------------|
{self._format_performance_markdown(perf)}

"""

        # Format recommendations
        recommendations = "\n".join(f"- {rec}" for rec in report_data["recommendations"])

        return template.format(
            timestamp=report_data["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
            project_path=report_data["project_path"],
            total_tests=report_data["total_tests"],
            category_table=category_table,
            marker_table=marker_table,
            isolation_section=isolation_section,
            quality_section=quality_section,
            performance_section=performance_section,
            recommendations=recommendations
        )

    def _test_has_marker(self, test_file: str, marker: str) -> bool:
        """Check if a test file has a specific marker."""
        try:
            content = Path(test_file).read_text(encoding="utf-8")
            return f"@{marker}" in content or f"pytest.mark.{marker}" in content
        except (UnicodeDecodeError, OSError):
            return False

    def _calculate_severity_percentages(self, isolation_report: IsolationReport) -> Dict[str, float]:
        """Calculate severity percentages."""
        total = isolation_report.total_issues
        if total == 0:
            return {"high": 0.0, "medium": 0.0, "low": 0.0}

        return {
            "high": (isolation_report.issues_by_severity.get("high", 0) / total) * 100,
            "medium": (isolation_report.issues_by_severity.get("medium", 0) / total) * 100,
            "low": (isolation_report.issues_by_severity.get("low", 0) / total) * 100
        }

    def _generate_isolation_recommendations(self, isolation_report: IsolationReport) -> List[str]:
        """Generate isolation-specific recommendations."""
        recommendations = []

        if isolation_report.issues_by_type.get("global_state", 0) > 0:
            recommendations.append(
                "Consider using pytest fixtures for shared test data instead of global variables"
            )

        if isolation_report.issues_by_type.get("shared_resource", 0) > 0:
            recommendations.append(
                "Mock external dependencies (databases, APIs, file systems) to improve isolation"
            )

        if isolation_report.issues_by_severity.get("high", 0) > 0:
            recommendations.append(
                "Prioritize fixing high-severity isolation issues first"
            )

        return recommendations

    def _generate_comprehensive_recommendations(
        self,
        collection_results: Dict[str, Any],
        isolation_report: Optional[IsolationReport],
        quality_metrics: Optional[QualityMetrics],
        performance_metrics: Optional[PerformanceMetrics]
    ) -> List[str]:
        """Generate comprehensive recommendations."""
        recommendations = []

        # Test coverage recommendations
        total_tests = sum(len(tests) for tests in collection_results.values())
        if total_tests < 50:
            recommendations.append("Consider increasing test coverage for better code reliability")

        # Marker recommendations
        markerless_tests = 0
        for tests in collection_results.values():
            for test_file in tests:
                has_marker = False
                for marker in ["fast", "medium", "slow"]:
                    if self._test_has_marker(test_file, marker):
                        has_marker = True
                        break
                if not has_marker:
                    markerless_tests += 1

        if markerless_tests > 0:
            recommendations.append(
                f"Add speed markers (@fast, @medium, @slow) to {markerless_tests} unmarked tests"
            )

        # Isolation recommendations
        if isolation_report and isolation_report.total_issues > 0:
            recommendations.extend(self._generate_isolation_recommendations(isolation_report))

        # Quality recommendations
        if quality_metrics and quality_metrics.overall_score < 80:
            recommendations.append("Focus on improving overall test quality through better organization and documentation")

        # Performance recommendations
        if performance_metrics:
            if performance_metrics.collection_time > 5.0:
                recommendations.append("Consider optimizing test collection performance")
            if performance_metrics.analysis_time > 10.0:
                recommendations.append("Consider caching test analysis results for better performance")

        return recommendations

    def _prepare_for_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for JSON serialization."""
        json_data = {}

        for key, value in data.items():
            if isinstance(value, datetime):
                json_data[key] = value.isoformat()
            elif isinstance(value, Dict):
                json_data[key] = self._prepare_for_json(value)
            elif isinstance(value, List):
                json_data[key] = [self._prepare_for_json(item) if isinstance(item, Dict) else item for item in value]
            else:
                json_data[key] = value

        return json_data

    def _format_severity_rows(self, severity_data: Dict[str, int]) -> str:
        """Format severity data for HTML table."""
        return "\n".join(
            f'<tr><td>{severity}</td><td>{count}</td></tr>'
            for severity, count in severity_data.items()
        )

    def _format_quality_rows(self, quality_data: Dict[str, Any]) -> str:
        """Format quality data for HTML table."""
        rows = []
        for metric, score in quality_data.items():
            if isinstance(score, (int, float)):
                rows.append(f'<tr><td>{metric.replace("_", " ").title()}</td><td>{score}</td></tr>')
        return "\n".join(rows)

    def _format_performance_rows(self, performance_data: Dict[str, Any]) -> str:
        """Format performance data for HTML table."""
        rows = []
        for operation, time_value in performance_data.items():
            if isinstance(time_value, (int, float)):
                rows.append(f'<tr><td>{operation.replace("_", " ").title()}</td><td>{time_value:.2f}</td></tr>')
        return "\n".join(rows)

    def _format_severity_markdown(self, severity_data: Dict[str, int]) -> str:
        """Format severity data for Markdown table."""
        return "\n".join(
            f"| {severity} | {count} |"
            for severity, count in severity_data.items()
        )

    def _format_quality_markdown(self, quality_data: Dict[str, Any]) -> str:
        """Format quality data for Markdown table."""
        rows = []
        for metric, score in quality_data.items():
            if isinstance(score, (int, float)):
                rows.append(f"| {metric.replace('_', ' ').title()} | {score} |")
        return "\n".join(rows)

    def _format_performance_markdown(self, performance_data: Dict[str, Any]) -> str:
        """Format performance data for Markdown table."""
        rows = []
        for operation, time_value in performance_data.items():
            if isinstance(time_value, (int, float)):
                rows.append(f"| {operation.replace('_', ' ').title()} | {time_value:.2f} |")
        return "\n".join(rows)

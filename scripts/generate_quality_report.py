#!/usr/bin/env python3
"""
Quality Metrics Dashboard Generator

This script generates a comprehensive quality dashboard that combines metrics from
multiple sources including coverage, mutation testing, property tests, and more.

Usage:
    python scripts/generate_quality_report.py [OPTIONS]

Examples:
    # Generate basic quality report
    python scripts/generate_quality_report.py

    # Generate with mutation testing
    python scripts/generate_quality_report.py --include-mutations

    # Generate HTML dashboard
    python scripts/generate_quality_report.py --html test_reports/quality_dashboard.html

    # Set quality thresholds
    python scripts/generate_quality_report.py --coverage-threshold 85 --mutation-threshold 70
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add src to path to import DevSynth modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def get_coverage_metrics() -> Dict[str, Any]:
    """Get coverage metrics from existing coverage data."""
    try:
        coverage_file = Path("test_reports/coverage.json")
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

            return {
                "line_coverage": coverage_data.get("totals", {}).get(
                    "percent_covered", 0
                ),
                "branch_coverage": coverage_data.get("totals", {}).get(
                    "percent_covered_display", 0
                ),
                "num_statements": coverage_data.get("totals", {}).get(
                    "num_statements", 0
                ),
                "missing_lines": coverage_data.get("totals", {}).get(
                    "missing_lines", 0
                ),
                "covered_lines": coverage_data.get("totals", {}).get(
                    "covered_lines", 0
                ),
            }
    except Exception as e:
        logger.warning(f"Failed to get coverage metrics: {e}")

    return {
        "line_coverage": 0,
        "branch_coverage": 0,
        "num_statements": 0,
        "missing_lines": 0,
        "covered_lines": 0,
    }


def get_mutation_testing_metrics(include_mutations: bool = False) -> Dict[str, Any]:
    """Get mutation testing metrics."""
    if not include_mutations:
        return {
            "mutation_score": None,
            "total_mutations": 0,
            "killed_mutations": 0,
            "survived_mutations": 0,
            "skipped": True,
        }

    try:
        # Run mutation testing on a small subset for dashboard
        result = subprocess.run(
            [
                sys.executable,
                "scripts/run_mutation_testing.py",
                "--max-mutations",
                "25",
                "--timeout",
                "10",
                "src/devsynth/utils/",
                "tests/unit/utils/",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode == 0:
            # Parse output for mutation score
            output_lines = result.stdout.split("\n")
            for line in output_lines:
                if "Mutation score:" in line:
                    score_str = line.split(":")[-1].strip().rstrip("%")
                    try:
                        mutation_score = float(score_str)
                        return {
                            "mutation_score": mutation_score,
                            "total_mutations": 25,  # Limited for dashboard
                            "killed_mutations": int(25 * mutation_score / 100),
                            "survived_mutations": int(
                                25 * (100 - mutation_score) / 100
                            ),
                            "skipped": False,
                        }
                    except ValueError:
                        pass
    except Exception as e:
        logger.warning(f"Failed to run mutation testing: {e}")

    return {
        "mutation_score": 0,
        "total_mutations": 0,
        "killed_mutations": 0,
        "survived_mutations": 0,
        "skipped": False,
    }


def get_property_test_metrics() -> Dict[str, Any]:
    """Get property-based test metrics."""
    try:
        # Count property tests
        property_dir = Path("tests/property")
        if property_dir.exists():
            property_files = list(property_dir.glob("test_*.py"))

            total_property_tests = 0
            for file in property_files:
                with open(file) as f:
                    content = f.read()
                    total_property_tests += content.count("@given(")

            return {
                "total_property_tests": total_property_tests,
                "property_test_files": len(property_files),
                "enabled": os.environ.get("DEVSYNTH_PROPERTY_TESTING", "0") == "1",
            }
    except Exception as e:
        logger.warning(f"Failed to get property test metrics: {e}")

    return {"total_property_tests": 0, "property_test_files": 0, "enabled": False}


def get_test_organization_metrics() -> Dict[str, Any]:
    """Get test organization and marker metrics."""
    try:
        result = subprocess.run(
            [sys.executable, "scripts/verify_test_markers.py", "--json"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return {
                "total_tests": data.get("total_tests", 0),
                "tests_with_speed_markers": data.get("tests_with_speed_markers", 0),
                "tests_with_isolation_markers": data.get(
                    "tests_with_isolation_markers", 0
                ),
                "marker_compliance": data.get("marker_compliance_percentage", 0),
                "issues_found": len(data.get("issues", [])),
            }
    except Exception as e:
        logger.warning(f"Failed to get test organization metrics: {e}")

    return {
        "total_tests": 0,
        "tests_with_speed_markers": 0,
        "tests_with_isolation_markers": 0,
        "marker_compliance": 0,
        "issues_found": 0,
    }


def get_performance_metrics() -> Dict[str, Any]:
    """Get test execution performance metrics."""
    try:
        # Check if benchmark results exist
        benchmark_file = Path("test_reports/benchmark_results.json")
        if benchmark_file.exists():
            with open(benchmark_file) as f:
                benchmark_data = json.load(f)
                return benchmark_data.get("performance_summary", {})
    except Exception as e:
        logger.warning(f"Failed to get performance metrics: {e}")

    return {
        "parallel_speedup": 0,
        "execution_time_seconds": 0,
        "efficiency": 0,
        "worker_count": 0,
    }


def calculate_overall_quality_score(metrics: Dict[str, Any]) -> float:
    """Calculate a weighted overall quality score."""
    weights = {
        "coverage": 0.3,
        "mutation": 0.25,
        "property": 0.15,
        "organization": 0.15,
        "performance": 0.15,
    }

    # Coverage score (0-100)
    coverage_score = metrics["coverage"]["line_coverage"]

    # Mutation score (0-100, or 0 if skipped)
    mutation_score = metrics["mutation"]["mutation_score"] or 0

    # Property test score (based on presence and enablement)
    property_score = 0
    if metrics["property"]["total_property_tests"] > 0:
        property_score = 70 if metrics["property"]["enabled"] else 40

    # Organization score (marker compliance)
    organization_score = metrics["organization"]["marker_compliance"]

    # Performance score (based on parallel speedup)
    performance_speedup = metrics["performance"]["parallel_speedup"]
    performance_score = (
        min(100, performance_speedup * 20) if performance_speedup > 0 else 50
    )

    # Calculate weighted average
    overall_score = (
        weights["coverage"] * coverage_score
        + weights["mutation"] * mutation_score
        + weights["property"] * property_score
        + weights["organization"] * organization_score
        + weights["performance"] * performance_score
    )

    return round(overall_score, 2)


def generate_quality_recommendations(metrics: Dict[str, Any]) -> List[str]:
    """Generate actionable quality improvement recommendations."""
    recommendations = []

    # Coverage recommendations
    coverage = metrics["coverage"]["line_coverage"]
    if coverage < 80:
        recommendations.append(
            f"📈 Increase test coverage from {coverage:.1f}% to at least 80%"
        )
    elif coverage < 90:
        recommendations.append(
            f"🎯 Excellent coverage at {coverage:.1f}% - consider targeting 90%"
        )

    # Mutation testing recommendations
    if metrics["mutation"]["skipped"]:
        recommendations.append(
            "🧬 Enable mutation testing to assess test quality beyond coverage"
        )
    elif (
        metrics["mutation"]["mutation_score"]
        and metrics["mutation"]["mutation_score"] < 70
    ):
        recommendations.append(
            f"🔬 Improve mutation score from {metrics['mutation']['mutation_score']:.1f}% to 70%+"
        )

    # Property testing recommendations
    if metrics["property"]["total_property_tests"] == 0:
        recommendations.append("🎲 Add property-based tests for critical algorithms")
    elif not metrics["property"]["enabled"]:
        recommendations.append(
            "⚡ Enable property testing with DEVSYNTH_PROPERTY_TESTING=1"
        )

    # Organization recommendations
    if metrics["organization"]["marker_compliance"] < 95:
        recommendations.append(
            "🏷️ Improve test marker compliance for better organization"
        )

    # Performance recommendations
    speedup = metrics["performance"]["parallel_speedup"]
    if speedup < 3:
        recommendations.append(
            "🚀 Optimize parallel test execution for better performance"
        )

    return recommendations


def generate_html_dashboard(metrics: Dict[str, Any], output_file: str) -> None:
    """Generate an HTML quality dashboard."""
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DevSynth Quality Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{ background: white; padding: 30px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header h1 {{ margin: 0; color: #333; }}
        .header .subtitle {{ color: #666; margin-top: 10px; }}
        .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }}
        .metric-card {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .metric-card h3 {{ margin: 0 0 15px 0; color: #333; }}
        .metric-value {{ font-size: 2em; font-weight: bold; margin: 10px 0; }}
        .metric-good {{ color: #28a745; }}
        .metric-warning {{ color: #ffc107; }}
        .metric-danger {{ color: #dc3545; }}
        .progress-bar {{ background: #e9ecef; height: 10px; border-radius: 5px; overflow: hidden; margin: 10px 0; }}
        .progress-fill {{ height: 100%; transition: width 0.3s ease; }}
        .recommendations {{ background: white; padding: 25px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .recommendations h3 {{ margin: 0 0 20px 0; color: #333; }}
        .recommendation {{ padding: 10px; margin: 10px 0; background: #f8f9fa; border-left: 4px solid #007bff; border-radius: 4px; }}
        .timestamp {{ color: #666; font-size: 0.9em; text-align: right; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 DevSynth Quality Dashboard</h1>
            <div class="subtitle">Comprehensive testing quality metrics and insights</div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <h3>📊 Overall Quality Score</h3>
                <div class="metric-value {'metric-good' if metrics['overall_score'] >= 80 else 'metric-warning' if metrics['overall_score'] >= 60 else 'metric-danger'}">{metrics['overall_score']:.1f}/100</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {metrics['overall_score']}%; background: {'#28a745' if metrics['overall_score'] >= 80 else '#ffc107' if metrics['overall_score'] >= 60 else '#dc3545'};"></div>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>📈 Test Coverage</h3>
                <div class="metric-value {'metric-good' if metrics['coverage']['line_coverage'] >= 80 else 'metric-warning' if metrics['coverage']['line_coverage'] >= 60 else 'metric-danger'}">{metrics['coverage']['line_coverage']:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {metrics['coverage']['line_coverage']}%; background: {'#28a745' if metrics['coverage']['line_coverage'] >= 80 else '#ffc107' if metrics['coverage']['line_coverage'] >= 60 else '#dc3545'};"></div>
                </div>
                <div>{metrics['coverage']['covered_lines']:,} / {metrics['coverage']['num_statements']:,} lines covered</div>
            </div>
            
            <div class="metric-card">
                <h3>🧬 Mutation Testing</h3>
                {'<div class="metric-value metric-warning">Skipped</div>' if metrics['mutation']['skipped'] else f'<div class="metric-value {"metric-good" if (metrics["mutation"]["mutation_score"] or 0) >= 70 else "metric-warning" if (metrics["mutation"]["mutation_score"] or 0) >= 50 else "metric-danger"}">{metrics["mutation"]["mutation_score"] or 0:.1f}%</div>'}
                {'' if metrics['mutation']['skipped'] else f'<div class="progress-bar"><div class="progress-fill" style="width: {metrics["mutation"]["mutation_score"] or 0}%; background: {"#28a745" if (metrics["mutation"]["mutation_score"] or 0) >= 70 else "#ffc107" if (metrics["mutation"]["mutation_score"] or 0) >= 50 else "#dc3545"};"></div></div>'}
                <div>{metrics['mutation']['killed_mutations']} / {metrics['mutation']['total_mutations']} mutations killed</div>
            </div>
            
            <div class="metric-card">
                <h3>🎲 Property Testing</h3>
                <div class="metric-value {'metric-good' if metrics['property']['total_property_tests'] > 0 else 'metric-warning'}">{metrics['property']['total_property_tests']}</div>
                <div>{metrics['property']['property_test_files']} property test files</div>
                <div>Status: {'✅ Enabled' if metrics['property']['enabled'] else '⚠️ Disabled'}</div>
            </div>
            
            <div class="metric-card">
                <h3>🏷️ Test Organization</h3>
                <div class="metric-value {'metric-good' if metrics['organization']['marker_compliance'] >= 95 else 'metric-warning' if metrics['organization']['marker_compliance'] >= 80 else 'metric-danger'}">{metrics['organization']['marker_compliance']:.1f}%</div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {metrics['organization']['marker_compliance']}%; background: {'#28a745' if metrics['organization']['marker_compliance'] >= 95 else '#ffc107' if metrics['organization']['marker_compliance'] >= 80 else '#dc3545'};"></div>
                </div>
                <div>{metrics['organization']['total_tests']:,} total tests</div>
            </div>
            
            <div class="metric-card">
                <h3>🚀 Performance</h3>
                <div class="metric-value {'metric-good' if metrics['performance']['parallel_speedup'] >= 3 else 'metric-warning' if metrics['performance']['parallel_speedup'] >= 2 else 'metric-danger'}">{metrics['performance']['parallel_speedup']:.1f}x</div>
                <div>Parallel speedup with {metrics['performance']['worker_count']} workers</div>
                <div>Efficiency: {metrics['performance']['efficiency']:.2f}</div>
            </div>
        </div>
        
        <div class="recommendations">
            <h3>💡 Quality Improvement Recommendations</h3>
            {''.join(f'<div class="recommendation">{rec}</div>' for rec in metrics['recommendations'])}
        </div>
        
        <div class="timestamp">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

    with open(output_file, "w") as f:
        f.write(html_content)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive quality metrics dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--output",
        "-o",
        default="test_reports/quality_report.json",
        help="Output file for JSON report",
    )

    parser.add_argument("--html", help="Generate HTML dashboard at specified path")

    parser.add_argument(
        "--include-mutations",
        action="store_true",
        help="Include mutation testing metrics (slower)",
    )

    parser.add_argument(
        "--coverage-threshold",
        type=float,
        default=80.0,
        help="Coverage threshold for quality scoring",
    )

    parser.add_argument(
        "--mutation-threshold",
        type=float,
        default=70.0,
        help="Mutation score threshold for quality scoring",
    )

    args = parser.parse_args()

    print("🧪 Generating Quality Metrics Dashboard...")
    print("=" * 60)

    # Collect metrics from various sources
    print("📊 Collecting coverage metrics...")
    coverage_metrics = get_coverage_metrics()

    print("🧬 Collecting mutation testing metrics...")
    mutation_metrics = get_mutation_testing_metrics(args.include_mutations)

    print("🎲 Collecting property test metrics...")
    property_metrics = get_property_test_metrics()

    print("🏷️ Collecting test organization metrics...")
    organization_metrics = get_test_organization_metrics()

    print("🚀 Collecting performance metrics...")
    performance_metrics = get_performance_metrics()

    # Combine all metrics
    all_metrics = {
        "timestamp": datetime.now().isoformat(),
        "coverage": coverage_metrics,
        "mutation": mutation_metrics,
        "property": property_metrics,
        "organization": organization_metrics,
        "performance": performance_metrics,
    }

    # Calculate overall quality score
    print("🎯 Calculating overall quality score...")
    overall_score = calculate_overall_quality_score(all_metrics)
    all_metrics["overall_score"] = overall_score

    # Generate recommendations
    print("💡 Generating quality recommendations...")
    recommendations = generate_quality_recommendations(all_metrics)
    all_metrics["recommendations"] = recommendations

    # Save JSON report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(all_metrics, f, indent=2)

    # Generate HTML dashboard if requested
    if args.html:
        print(f"📄 Generating HTML dashboard: {args.html}")
        os.makedirs(os.path.dirname(args.html), exist_ok=True)
        generate_html_dashboard(all_metrics, args.html)

    # Print summary
    print("\n" + "=" * 60)
    print("🎯 QUALITY DASHBOARD SUMMARY")
    print("=" * 60)
    print(f"Overall Quality Score: {overall_score:.1f}/100")
    print(f"Coverage: {coverage_metrics['line_coverage']:.1f}%")
    if not mutation_metrics["skipped"]:
        print(f"Mutation Score: {mutation_metrics['mutation_score']:.1f}%")
    print(f"Property Tests: {property_metrics['total_property_tests']}")
    print(f"Test Organization: {organization_metrics['marker_compliance']:.1f}%")
    print(f"Parallel Speedup: {performance_metrics['parallel_speedup']:.1f}x")

    print(f"\n📄 Report saved to: {args.output}")
    if args.html:
        print(f"📊 Dashboard saved to: {args.html}")

    print("\n💡 Top Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

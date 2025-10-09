#!/usr/bin/env python3
"""
Performance Baseline Measurement Tool

This script measures current parallel test execution performance with different
worker counts and test categories. It identifies slowest tests and bottlenecks
to establish a performance baseline for optimization tracking.

Usage:
    python scripts/benchmark_test_execution.py [--output FILE] [--workers LIST] [--targets LIST]

Examples:
    # Basic benchmark with default settings
    python scripts/benchmark_test_execution.py

    # Custom worker counts and targets
    python scripts/benchmark_test_execution.py --workers 1,2,4,8 --targets unit-tests,integration-tests

    # Save to custom file
    python scripts/benchmark_test_execution.py --output benchmark_results.json
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TestExecutionBenchmark:
    """Benchmarks test execution performance."""

    def __init__(self) -> None:
        self.results: Dict[str, Any] = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "tool_version": "1.0.0",
                "python_version": sys.version,
                "platform": os.uname().sysname if hasattr(os, "uname") else "unknown",
            },
            "benchmarks": [],
            "analysis": {},
        }

    def run_benchmark(
        self,
        target: str,
        speed: Optional[str] = None,
        workers: int = 1,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """Run a single benchmark test."""
        print(f"  Running {target} (speed: {speed or 'all'}, workers: {workers})...")

        # Build command
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--no-cov",  # Disable coverage for pure performance measurement
            "--tb=no",  # Minimal output for cleaner timing
            "-q",  # Quiet mode
        ]

        # Add worker specification
        if workers > 1:
            cmd.extend(["-n", str(workers)])
        else:
            cmd.extend(["-n", "0"])  # Explicitly disable xdist

        # Add target specification
        if target == "unit-tests":
            cmd.append("tests/unit")
        elif target == "integration-tests":
            cmd.append("tests/integration")
        elif target == "behavior-tests":
            cmd.append("tests/behavior")
        elif target == "all-tests":
            cmd.append("tests")
        else:
            cmd.append(target)  # Custom path

        # Add speed filter
        if speed:
            cmd.extend(["-m", speed])

        # Set environment for consistent testing
        env = os.environ.copy()
        env["DEVSYNTH_NO_FILE_LOGGING"] = "1"
        env["DEVSYNTH_OFFLINE"] = "true"
        env["DEVSYNTH_PROVIDER"] = "stub"

        # Disable optional resources for consistent timing
        env["DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE"] = "false"
        env["DEVSYNTH_RESOURCE_OPENAI_AVAILABLE"] = "false"
        env["DEVSYNTH_RESOURCE_ANTHROPIC_AVAILABLE"] = "false"

        start_time = time.time()

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env,
                cwd=Path.cwd(),
            )

            end_time = time.time()
            duration = end_time - start_time

            # Parse output for test counts
            output_lines = result.stdout.split("\n")
            test_count = 0
            passed = 0
            failed = 0
            skipped = 0

            for line in output_lines:
                if "passed" in line and (
                    "failed" in line or "skipped" in line or "error" in line
                ):
                    # Parse summary line like "1 failed, 2 passed, 3 skipped in 1.23s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            try:
                                passed = int(parts[i - 1])
                            except:
                                pass
                        elif part == "failed" and i > 0:
                            try:
                                failed = int(parts[i - 1])
                            except:
                                pass
                        elif part == "skipped" and i > 0:
                            try:
                                skipped = int(parts[i - 1])
                            except:
                                pass

            test_count = passed + failed + skipped

            return {
                "target": target,
                "speed": speed,
                "workers": workers,
                "duration": duration,
                "success": result.returncode == 0,
                "test_count": test_count,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "tests_per_second": test_count / duration if duration > 0 else 0,
                "command": " ".join(cmd),
                "stdout_lines": len(output_lines),
                "stderr_lines": len(result.stderr.split("\n")) if result.stderr else 0,
            }

        except subprocess.TimeoutExpired:
            return {
                "target": target,
                "speed": speed,
                "workers": workers,
                "duration": timeout,
                "success": False,
                "error": "timeout",
                "test_count": 0,
                "tests_per_second": 0,
            }
        except Exception as e:
            return {
                "target": target,
                "speed": speed,
                "workers": workers,
                "duration": 0,
                "success": False,
                "error": str(e),
                "test_count": 0,
                "tests_per_second": 0,
            }

    def run_comprehensive_benchmark(
        self, targets: List[str], worker_counts: List[int], timeout: int = 300
    ) -> None:
        """Run comprehensive benchmarks across targets and worker counts."""
        print(f"Running comprehensive benchmark...")
        print(f"Targets: {targets}")
        print(f"Worker counts: {worker_counts}")

        total_benchmarks = len(targets) * len(worker_counts)
        current = 0

        for target in targets:
            for workers in worker_counts:
                current += 1
                print(
                    f"[{current}/{total_benchmarks}] Benchmarking {target} with {workers} workers..."
                )

                benchmark_result = self.run_benchmark(target, None, workers, timeout)
                self.results["benchmarks"].append(benchmark_result)

                # Also run fast tests separately for more granular analysis
                if target in ["unit-tests", "all-tests"]:
                    print(
                        f"[{current}/{total_benchmarks}] Benchmarking {target}/fast with {workers} workers..."
                    )
                    fast_result = self.run_benchmark(target, "fast", workers, timeout)
                    self.results["benchmarks"].append(fast_result)

    def analyze_results(self) -> None:
        """Analyze benchmark results and generate insights."""
        if not self.results["benchmarks"]:
            return

        # Group results by target and workers
        by_target = {}
        by_workers = {}

        for benchmark in self.results["benchmarks"]:
            target = benchmark["target"]
            workers = benchmark["workers"]

            if target not in by_target:
                by_target[target] = []
            by_target[target].append(benchmark)

            if workers not in by_workers:
                by_workers[workers] = []
            by_workers[workers].append(benchmark)

        # Calculate speedup ratios
        speedup_analysis = {}
        for target, benchmarks in by_target.items():
            target_analysis = {"benchmarks": benchmarks, "speedups": {}}

            # Find baseline (1 worker)
            baseline = next((b for b in benchmarks if b["workers"] == 1), None)
            if baseline and baseline["duration"] > 0:
                for benchmark in benchmarks:
                    if benchmark["workers"] != 1 and benchmark["duration"] > 0:
                        speedup = baseline["duration"] / benchmark["duration"]
                        target_analysis["speedups"][benchmark["workers"]] = {
                            "speedup": speedup,
                            "efficiency": speedup / benchmark["workers"],
                            "baseline_duration": baseline["duration"],
                            "parallel_duration": benchmark["duration"],
                        }

            speedup_analysis[target] = target_analysis

        # Find bottlenecks
        bottlenecks = []
        for benchmark in self.results["benchmarks"]:
            if benchmark["success"] and benchmark["duration"] > 30:  # Slow tests
                bottlenecks.append(
                    {
                        "target": benchmark["target"],
                        "speed": benchmark.get("speed", "all"),
                        "workers": benchmark["workers"],
                        "duration": benchmark["duration"],
                        "tests_per_second": benchmark.get("tests_per_second", 0),
                    }
                )

        # Overall statistics
        successful_benchmarks = [b for b in self.results["benchmarks"] if b["success"]]
        if successful_benchmarks:
            durations = [b["duration"] for b in successful_benchmarks]
            test_counts = [b["test_count"] for b in successful_benchmarks]

            stats = {
                "total_benchmarks": len(self.results["benchmarks"]),
                "successful_benchmarks": len(successful_benchmarks),
                "average_duration": sum(durations) / len(durations),
                "min_duration": min(durations),
                "max_duration": max(durations),
                "total_tests_measured": sum(test_counts),
                "average_test_count": (
                    sum(test_counts) / len(test_counts) if test_counts else 0
                ),
            }
        else:
            stats = {
                "total_benchmarks": len(self.results["benchmarks"]),
                "successful_benchmarks": 0,
                "error": "No successful benchmarks",
            }

        self.results["analysis"] = {
            "speedup_analysis": speedup_analysis,
            "bottlenecks": sorted(
                bottlenecks, key=lambda x: x["duration"], reverse=True
            ),
            "statistics": stats,
            "recommendations": self._generate_recommendations(
                speedup_analysis, bottlenecks
            ),
        }

    def _generate_recommendations(
        self, speedup_analysis: Dict, bottlenecks: List
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Analyze speedup efficiency
        for target, analysis in speedup_analysis.items():
            speedups = analysis.get("speedups", {})
            if speedups:
                max_workers = max(speedups.keys())
                max_speedup = speedups[max_workers]["speedup"]
                max_efficiency = speedups[max_workers]["efficiency"]

                if max_speedup < 2.0:
                    recommendations.append(
                        f"{target}: Poor parallelization (max {max_speedup:.1f}x speedup with {max_workers} workers)"
                    )
                elif max_efficiency < 0.5:
                    recommendations.append(
                        f"{target}: Low efficiency ({max_efficiency:.1f}) suggests overhead issues"
                    )
                else:
                    recommendations.append(
                        f"{target}: Good parallelization ({max_speedup:.1f}x speedup with {max_workers} workers)"
                    )

        # Analyze bottlenecks
        if bottlenecks:
            recommendations.append(
                f"Found {len(bottlenecks)} slow test executions (>30s)"
            )
            for bottleneck in bottlenecks[:3]:  # Top 3
                recommendations.append(
                    f"  - {bottleneck['target']}/{bottleneck['speed']}: {bottleneck['duration']:.1f}s"
                )

        return recommendations


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Benchmark test execution performance",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("test_reports/performance_baseline.json"),
        help="Output file for benchmark results (default: test_reports/performance_baseline.json)",
    )

    parser.add_argument(
        "--workers",
        type=str,
        default="1,2,4",
        help="Comma-separated list of worker counts to test (default: 1,2,4)",
    )

    parser.add_argument(
        "--targets",
        type=str,
        default="unit-tests",
        help="Comma-separated list of test targets (default: unit-tests)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout per benchmark in seconds (default: 300)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick benchmark (fast tests only, fewer workers)",
    )

    args = parser.parse_args()

    # Parse worker counts
    try:
        worker_counts = [int(w.strip()) for w in args.workers.split(",")]
    except ValueError:
        print(f"Error: Invalid worker counts: {args.workers}")
        return 1

    # Parse targets
    targets = [t.strip() for t in args.targets.split(",")]

    # Quick mode adjustments
    if args.quick:
        worker_counts = [1, 2]
        targets = ["unit-tests"]
        print("Quick mode: limiting to unit-tests with 1,2 workers")

    # Ensure output directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Run benchmarks
    benchmark = TestExecutionBenchmark()

    try:
        benchmark.run_comprehensive_benchmark(targets, worker_counts, args.timeout)
        benchmark.analyze_results()

        # Save results
        with open(args.output, "w") as f:
            json.dump(benchmark.results, f, indent=2, sort_keys=True)

        # Print summary
        print(f"\nBenchmark complete! Results saved to {args.output}")

        analysis = benchmark.results.get("analysis", {})
        stats = analysis.get("statistics", {})

        if stats:
            print(f"\nSummary:")
            print(f"  Total benchmarks: {stats['total_benchmarks']}")
            print(f"  Successful: {stats['successful_benchmarks']}")
            if "average_duration" in stats:
                print(f"  Average duration: {stats['average_duration']:.2f}s")
                print(
                    f"  Range: {stats['min_duration']:.2f}s - {stats['max_duration']:.2f}s"
                )
                print(f"  Total tests: {stats['total_tests_measured']}")

        recommendations = analysis.get("recommendations", [])
        if recommendations:
            print(f"\nRecommendations:")
            for rec in recommendations:
                print(f"  - {rec}")

        # Show speedup analysis
        speedup_analysis = analysis.get("speedup_analysis", {})
        if speedup_analysis:
            print(f"\nSpeedup Analysis:")
            for target, target_analysis in speedup_analysis.items():
                speedups = target_analysis.get("speedups", {})
                if speedups:
                    print(f"  {target}:")
                    for workers, speedup_data in speedups.items():
                        speedup = speedup_data["speedup"]
                        efficiency = speedup_data["efficiency"]
                        print(
                            f"    {workers} workers: {speedup:.2f}x speedup ({efficiency:.2f} efficiency)"
                        )

        return 0

    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running benchmark: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

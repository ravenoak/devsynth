#!/usr/bin/env python3
"""
Mutation Testing CLI

Command-line interface for running mutation testing on DevSynth code.
This script provides a standalone way to run mutation testing with
configurable options and detailed reporting.

Usage:
    python scripts/run_mutation_testing.py [OPTIONS] TARGET_PATH TEST_PATH

Examples:
    # Test core utilities
    python scripts/run_mutation_testing.py src/devsynth/utils/ tests/unit/utils/

    # Test with limited mutations
    python scripts/run_mutation_testing.py --max-mutations 50 src/devsynth/core/ tests/unit/core/

    # Generate HTML report
    python scripts/run_mutation_testing.py --html-report test_reports/mutations.html src/devsynth/config/ tests/unit/config/
"""

import argparse
import sys
from pathlib import Path

# Add src to path to import mutation testing framework
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from devsynth.testing.mutation_testing import MutationTester


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run mutation testing on DevSynth code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("target_path", help="Path to source code to mutate")

    parser.add_argument("test_path", help="Path to tests that should catch mutations")

    parser.add_argument(
        "--max-mutations",
        type=int,
        help="Maximum number of mutations to test (default: no limit)",
    )

    parser.add_argument(
        "--module-filter", help="Only mutate files containing this string in their path"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="Timeout per mutation test in seconds (default: 30)",
    )

    parser.add_argument("--json-report", type=Path, help="Output JSON report file")

    parser.add_argument("--html-report", type=Path, help="Output HTML report file")

    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Minimum mutation score threshold (default: 0.8)",
    )

    args = parser.parse_args()

    # Validate paths
    if not Path(args.target_path).exists():
        print(f"Error: Target path does not exist: {args.target_path}")
        return 1

    if not Path(args.test_path).exists():
        print(f"Error: Test path does not exist: {args.test_path}")
        return 1

    # Set up default output paths
    if not args.json_report:
        args.json_report = Path("test_reports") / "mutation_testing_report.json"

    if not args.html_report:
        args.html_report = Path("test_reports") / "mutation_testing_report.html"

    # Ensure output directories exist
    args.json_report.parent.mkdir(parents=True, exist_ok=True)
    args.html_report.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting mutation testing...")
    print(f"Target: {args.target_path}")
    print(f"Tests: {args.test_path}")
    print(f"Max mutations: {args.max_mutations or 'unlimited'}")
    print(f"Timeout: {args.timeout}s")
    print()

    try:
        # Run mutation testing
        tester = MutationTester(timeout_seconds=args.timeout)
        report = tester.run_mutations(
            args.target_path,
            args.test_path,
            max_mutations=args.max_mutations,
            module_filter=args.module_filter,
        )

        # Save reports
        tester.save_json_report(report, args.json_report)
        tester.generate_html_report(report, args.html_report)

        # Print results
        print(f"Mutation testing complete!")
        print(f"JSON report: {args.json_report}")
        print(f"HTML report: {args.html_report}")
        print()
        print(f"Results:")
        print(f"  Total mutations: {report.total_mutations}")
        print(f"  Killed mutations: {report.killed_mutations}")
        print(f"  Survived mutations: {report.survived_mutations}")
        print(f"  Mutation score: {report.mutation_score:.2%}")
        print(f"  Execution time: {report.execution_time:.2f}s")
        print()

        # Show mutation type breakdown
        print("Mutation type breakdown:")
        for mut_type, stats in report.summary["mutation_types"].items():
            score = (stats["killed"] / stats["total"]) if stats["total"] > 0 else 0
            print(f"  {mut_type}: {stats['killed']}/{stats['total']} ({score:.2%})")

        # Show files with low mutation scores
        print("\nFiles needing attention (low mutation scores):")
        for file_path, stats in report.summary["file_breakdown"].items():
            score = (stats["killed"] / stats["total"]) if stats["total"] > 0 else 0
            if (
                score < args.threshold and stats["total"] >= 3
            ):  # Only show files with multiple mutations
                print(
                    f"  {file_path}: {stats['killed']}/{stats['total']} ({score:.2%})"
                )

        # Exit with appropriate code
        if report.mutation_score >= args.threshold:
            print(
                f"\n✓ Mutation score {report.mutation_score:.2%} meets threshold {args.threshold:.2%}"
            )
            return 0
        else:
            print(
                f"\n✗ Mutation score {report.mutation_score:.2%} below threshold {args.threshold:.2%}"
            )
            return 1

    except KeyboardInterrupt:
        print("\nMutation testing interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running mutation testing: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

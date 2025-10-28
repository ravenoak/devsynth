#!/usr/bin/env python3
"""
Extract Isolation Issues

This script extracts shared resource and missing teardown issues from an isolation report.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def extract_issues(report_path: str) -> dict[str, list[dict[str, Any]]]:
    """
    Extract shared resource and missing teardown issues from an isolation report.

    Args:
        report_path: Path to the isolation report JSON file

    Returns:
        Dictionary with shared resource and missing teardown issues
    """
    # Read the report file
    with open(report_path) as f:
        report = json.load(f)

    # Initialize result
    result = {"shared_resource": [], "missing_teardown": []}

    # Run test_isolation_analyzer.py on specific files with issues to get detailed reports
    files_with_issues = []
    for file_data in report.get("files", []):
        if file_data.get("issues_count", 0) > 0:
            files_with_issues.append(file_data.get("file", ""))

    # Process each file with issues
    for file_path in files_with_issues:
        try:
            # Run test_isolation_analyzer.py on the file with verbose output
            import subprocess

            cmd = [
                "python",
                "scripts/test_isolation_analyzer.py",
                "--file",
                file_path,
                "--verbose",
            ]
            process = subprocess.run(cmd, capture_output=True, text=True)
            output = process.stdout

            # Parse the output to extract issues
            lines = output.split("\n")
            current_issue = None

            for line in lines:
                if "shared_resource" in line and "message" in line:
                    # Extract file, line, message, function, and class from the output
                    parts = line.split(":")
                    if len(parts) >= 2:
                        message = parts[1].strip()
                        # Extract function and class if available
                        function = ""
                        class_name = ""
                        if "in method" in message:
                            parts = message.split("in method")
                            if len(parts) >= 2:
                                function = parts[1].strip()
                        elif "in function" in message:
                            parts = message.split("in function")
                            if len(parts) >= 2:
                                function = parts[1].strip()

                        result["shared_resource"].append(
                            {
                                "file": file_path,
                                "line": 0,  # Line number not available in this format
                                "message": message,
                                "function": function,
                                "class": class_name,
                            }
                        )

                if "missing_teardown" in line and "message" in line:
                    # Extract file, line, message, function, and class from the output
                    parts = line.split(":")
                    if len(parts) >= 2:
                        message = parts[1].strip()
                        # Extract class name from message
                        class_name = ""
                        if "Class" in message:
                            parts = message.split("Class")
                            if len(parts) >= 2:
                                class_name = parts[1].strip().split()[0]

                        result["missing_teardown"].append(
                            {
                                "file": file_path,
                                "line": 0,  # Line number not available in this format
                                "message": message,
                                "function": "",
                                "class": class_name,
                            }
                        )

        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    # If no issues were found using the above method, try a simpler approach
    if not result["shared_resource"] and not result["missing_teardown"]:
        print("No issues found using detailed analysis. Trying simpler approach...")

        # Just list the files with issues based on the report
        for file_data in report.get("files", []):
            file_path = file_data.get("file", "")
            issues_count = file_data.get("issues_count", 0)

            if issues_count > 0:
                # Check if any recommendations mention shared resources or teardown
                recommendations = file_data.get("recommendations", [])
                has_shared_resource = any(
                    "shared resource" in r.lower() for r in recommendations
                )
                has_missing_teardown = any(
                    "teardown" in r.lower() for r in recommendations
                )

                if has_shared_resource:
                    result["shared_resource"].append(
                        {
                            "file": file_path,
                            "line": 0,
                            "message": "Potential shared resource issue based on recommendations",
                            "function": "",
                            "class": "",
                        }
                    )

                if has_missing_teardown:
                    result["missing_teardown"].append(
                        {
                            "file": file_path,
                            "line": 0,
                            "message": "Potential missing teardown issue based on recommendations",
                            "function": "",
                            "class": "",
                        }
                    )

    return result


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python extract_isolation_issues.py <report_path>")
        sys.exit(1)

    report_path = sys.argv[1]

    # Extract issues
    issues = extract_issues(report_path)

    # Print shared resource issues
    print("\nShared Resource Issues:")
    print("======================")
    for i, issue in enumerate(issues["shared_resource"], 1):
        print(f"{i}. File: {issue['file']}")
        print(f"   Line: {issue['line']}")
        print(f"   Message: {issue['message']}")
        print(f"   Function: {issue['function']}")
        print(f"   Class: {issue['class']}")
        print()

    # Print missing teardown issues
    print("\nMissing Teardown Issues:")
    print("=======================")
    for i, issue in enumerate(issues["missing_teardown"], 1):
        print(f"{i}. File: {issue['file']}")
        print(f"   Line: {issue['line']}")
        print(f"   Message: {issue['message']}")
        print(f"   Function: {issue['function']}")
        print(f"   Class: {issue['class']}")
        print()


if __name__ == "__main__":
    main()

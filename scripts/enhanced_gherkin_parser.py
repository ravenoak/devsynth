#!/usr/bin/env python3
"""
Enhanced Gherkin Parser

This script provides a more robust parser for Gherkin feature files, with special handling
for Scenario Outlines and Examples. It's designed to accurately count the number of tests
that pytest-bdd would generate from feature files.

Usage:
    Import this module and use the parse_feature_file or parse_feature_directory functions.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


class GherkinParser:
    """Parser for Gherkin feature files."""

    def __init__(self, verbose: bool = False):
        """
        Initialize the parser.

        Args:
            verbose: Whether to show detailed information
        """
        self.verbose = verbose

    def parse_feature_file(self, file_path: str) -> dict[str, Any]:
        """
        Parse a Gherkin feature file.

        Args:
            file_path: Path to the feature file

        Returns:
            Dictionary with feature information
        """
        if self.verbose:
            print(f"Parsing feature file: {file_path}")

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Extract feature name
            feature_match = re.search(
                r"Feature:(.+?)(?=\n\s*(?:Background:|Scenario:|$))", content, re.DOTALL
            )
            feature_name = (
                feature_match.group(1).strip() if feature_match else "Unknown Feature"
            )

            # Extract background (if any)
            background_match = re.search(
                r"Background:(.+?)(?=\n\s*(?:Scenario:|$))", content, re.DOTALL
            )
            background = background_match.group(1).strip() if background_match else None

            # Extract scenarios
            scenarios = []

            # Regular scenarios
            scenario_matches = re.finditer(
                r"Scenario:(.+?)(?=\n\s*(?:Scenario:|Scenario Outline:|$))",
                content,
                re.DOTALL,
            )
            for match in scenario_matches:
                scenario_text = match.group(1).strip()
                scenario_name = scenario_text.split("\n")[0].strip()
                scenarios.append(
                    {
                        "type": "scenario",
                        "name": scenario_name,
                        "text": scenario_text,
                        "examples": None,
                    }
                )

            # Scenario outlines
            outline_matches = re.finditer(
                r"Scenario Outline:(.+?)(?=\n\s*(?:Scenario:|Scenario Outline:|$))",
                content,
                re.DOTALL,
            )
            for match in outline_matches:
                outline_text = match.group(1).strip()
                outline_name = outline_text.split("\n")[0].strip()

                # Extract examples
                examples_match = re.search(
                    r"Examples:(.+?)(?=\n\s*(?:Scenario:|Scenario Outline:|$)|$)",
                    outline_text,
                    re.DOTALL,
                )
                examples = []

                if examples_match:
                    examples_text = examples_match.group(1).strip()
                    examples_lines = examples_text.split("\n")

                    if len(examples_lines) >= 2:
                        # Parse header row
                        header_line = examples_lines[0].strip()
                        header_match = re.findall(r"\|\s*([^|]+?)\s*\|", header_line)
                        headers = [h.strip() for h in header_match]

                        # Parse data rows
                        for i in range(1, len(examples_lines)):
                            data_line = examples_lines[i].strip()
                            if not data_line or not re.match(r"\|", data_line):
                                continue

                            data_match = re.findall(r"\|\s*([^|]+?)\s*\|", data_line)
                            data = [d.strip() for d in data_match]

                            if len(data) == len(headers):
                                example = dict(zip(headers, data))
                                examples.append(example)

                scenarios.append(
                    {
                        "type": "outline",
                        "name": outline_name,
                        "text": outline_text,
                        "examples": examples,
                    }
                )

            return {
                "path": file_path,
                "name": feature_name,
                "background": background,
                "scenarios": scenarios,
            }

        except Exception as e:
            if self.verbose:
                print(f"Error parsing feature file {file_path}: {e}")
            return {
                "path": file_path,
                "name": "Error",
                "background": None,
                "scenarios": [],
                "error": str(e),
            }

    def parse_feature_directory(self, directory: str) -> list[dict[str, Any]]:
        """
        Parse all feature files in a directory.

        Args:
            directory: Directory to parse

        Returns:
            List of dictionaries with feature information
        """
        if self.verbose:
            print(f"Parsing feature directory: {directory}")

        features = []

        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith(".feature"):
                    file_path = os.path.join(root, file)
                    feature = self.parse_feature_file(file_path)
                    features.append(feature)

        return features

    def count_tests(self, features: list[dict[str, Any]]) -> int:
        """
        Count the number of tests that would be generated from the features.

        Args:
            features: List of feature dictionaries

        Returns:
            Number of tests
        """
        count = 0

        for feature in features:
            for scenario in feature.get("scenarios", []):
                if scenario["type"] == "scenario":
                    # Regular scenario = 1 test
                    count += 1
                elif scenario["type"] == "outline":
                    # Scenario outline = 1 test per example
                    examples = scenario.get("examples", [])
                    if examples:
                        count += len(examples)
                    else:
                        # If no examples, count as 1 test
                        count += 1

        return count

    def generate_test_paths(self, features: list[dict[str, Any]]) -> list[str]:
        """
        Generate test paths for all scenarios and examples.

        Args:
            features: List of feature dictionaries

        Returns:
            List of test paths
        """
        test_paths = []

        for feature in features:
            feature_path = feature["path"]

            for scenario in feature.get("scenarios", []):
                scenario_name = scenario["name"]

                if scenario["type"] == "scenario":
                    # Regular scenario
                    test_path = f"{feature_path}::{scenario_name}"
                    test_paths.append(test_path)

                elif scenario["type"] == "outline":
                    # Scenario outline
                    examples = scenario.get("examples", [])

                    if examples:
                        # Generate a test path for each example
                        for i, example in enumerate(examples):
                            # Create a string representation of the example values
                            example_str = "_".join(
                                f"{k}_{v}" for k, v in example.items()
                            )
                            test_path = (
                                f"{feature_path}::{scenario_name}::{example_str}"
                            )
                            test_paths.append(test_path)
                    else:
                        # If no examples, generate a single test path
                        test_path = f"{feature_path}::{scenario_name}"
                        test_paths.append(test_path)

        return test_paths


def parse_feature_file(file_path: str, verbose: bool = False) -> dict[str, Any]:
    """
    Parse a Gherkin feature file.

    Args:
        file_path: Path to the feature file
        verbose: Whether to show detailed information

    Returns:
        Dictionary with feature information
    """
    parser = GherkinParser(verbose=verbose)
    return parser.parse_feature_file(file_path)


def parse_feature_directory(
    directory: str, verbose: bool = False
) -> list[dict[str, Any]]:
    """
    Parse all feature files in a directory.

    Args:
        directory: Directory to parse
        verbose: Whether to show detailed information

    Returns:
        List of dictionaries with feature information
    """
    parser = GherkinParser(verbose=verbose)
    return parser.parse_feature_directory(directory)


def count_tests(features: list[dict[str, Any]]) -> int:
    """
    Count the number of tests that would be generated from the features.

    Args:
        features: List of feature dictionaries

    Returns:
        Number of tests
    """
    parser = GherkinParser()
    return parser.count_tests(features)


def generate_test_paths(features: list[dict[str, Any]]) -> list[str]:
    """
    Generate test paths for all scenarios and examples.

    Args:
        features: List of feature dictionaries

    Returns:
        List of test paths
    """
    parser = GherkinParser()
    return parser.generate_test_paths(features)


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python enhanced_gherkin_parser.py <feature_file_or_directory>")
        sys.exit(1)

    path = sys.argv[1]

    if os.path.isfile(path):
        feature = parse_feature_file(path, verbose=True)
        features = [feature]
    else:
        features = parse_feature_directory(path, verbose=True)

    test_count = count_tests(features)
    test_paths = generate_test_paths(features)

    print(f"Found {len(features)} feature files")
    print(f"Total test count: {test_count}")
    print(f"Generated {len(test_paths)} test paths")

    # Output detailed information as JSON
    output = {"features": features, "test_count": test_count, "test_paths": test_paths}

    with open("gherkin_parser_output.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"Detailed output written to gherkin_parser_output.json")

#!/usr/bin/env python3
"""
Script to guide manual testing of DevSynth CLI workflows.

This script walks the user through testing various CLI commands and workflows,
and records the results. It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/manual_cli_testing.py [--output FILENAME]

Options:
    --output FILENAME    Output file for test results (default: cli_test_results.md)
"""

import argparse
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from devsynth.testing.run_tests import run_tests


class CLIWorkflowTester:
    """Class to guide manual testing of CLI workflows."""

    def __init__(self, output_file="cli_test_results.md"):
        """
        Initialize the tester.

        Args:
            output_file (str): Path to the output file for test results
        """
        self.output_file = output_file
        self.results = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")

        # Create a temporary directory for testing
        self.test_dir = Path("./temp_cli_test")
        if not self.test_dir.exists():
            self.test_dir.mkdir(parents=True)

    def cleanup(self):
        """Clean up temporary files and directories."""
        import shutil

        if self.test_dir.exists():
            try:
                shutil.rmtree(self.test_dir)
                print(f"Cleaned up temporary directory: {self.test_dir}")
            except Exception as e:
                print(f"Error cleaning up temporary directory: {e}")

    def run_command(self, command):
        """
        Run a command and return the result.

        Args:
            command (str): Command to run

        Returns:
            tuple: (returncode, stdout, stderr)
        """
        try:
            process = subprocess.run(
                command, shell=True, check=False, capture_output=True, text=True
            )
            return process.returncode, process.stdout, process.stderr
        except Exception as e:
            return 1, "", str(e)

    def print_step(self, step_number, description):
        """
        Print a step in the testing process.

        Args:
            step_number (int): Step number
            description (str): Step description
        """
        print(f"\n{'='*80}")
        print(f"Step {step_number}: {description}")
        print(f"{'='*80}")

    def get_user_input(self, prompt, options=None):
        """
        Get input from the user.

        Args:
            prompt (str): Prompt to display
            options (list): List of valid options

        Returns:
            str: User input
        """
        while True:
            if options:
                option_str = "/".join(options)
                user_input = input(f"{prompt} [{option_str}]: ").strip().lower()
                if user_input in options:
                    return user_input
                print(f"Invalid input. Please enter one of: {option_str}")
            else:
                return input(f"{prompt}: ").strip()

    def record_result(self, test_name, command, result, notes=""):
        """
        Record a test result.

        Args:
            test_name (str): Name of the test
            command (str): Command that was run
            result (str): Result of the test (pass/fail)
            notes (str): Additional notes
        """
        self.results.append(
            {
                "test_name": test_name,
                "command": command,
                "result": result,
                "notes": notes,
            }
        )

    def save_results(self):
        """Save the test results to a file."""
        with open(self.output_file, "w") as f:
            f.write(f"# DevSynth CLI Workflow Test Results\n\n")
            f.write(f"Date: {self.current_date}\n\n")

            f.write("## Summary\n\n")

            # Count passes and fails
            passes = sum(1 for r in self.results if r["result"] == "pass")
            fails = sum(1 for r in self.results if r["result"] == "fail")
            total = len(self.results)

            f.write(f"- Total tests: {total}\n")
            f.write(f"- Passed: {passes}\n")
            f.write(f"- Failed: {fails}\n\n")

            f.write("## Detailed Results\n\n")

            for i, result in enumerate(self.results, 1):
                f.write(f"### {i}. {result['test_name']}\n\n")
                f.write(f"**Command:** `{result['command']}`\n\n")
                f.write(f"**Result:** {result['result'].upper()}\n\n")
                if result["notes"]:
                    f.write(f"**Notes:** {result['notes']}\n\n")
                f.write("---\n\n")

        print(f"\nTest results saved to {self.output_file}")

    def test_help_command(self):
        """Test the help command."""
        self.print_step(1, "Testing the help command")

        command = "devsynth help"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        result = self.get_user_input(
            "Did the help command display the expected output?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Help Command", command, result, notes)

    def test_init_command(self):
        """Test the init command."""
        self.print_step(2, "Testing the init command")

        # Change to the test directory
        os.chdir(self.test_dir)

        command = "devsynth init --path ./test_project"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        # Check if the project was created
        project_created = (
            Path("./test_project").exists()
            and Path("./test_project/.devsynth").exists()
        )

        if project_created:
            print("\nProject directory was created successfully.")
        else:
            print("\nProject directory was NOT created.")

        result = self.get_user_input(
            "Did the init command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("..")

        self.record_result("Init Command", command, result, notes)

    def test_spec_command(self):
        """Test the spec command."""
        self.print_step(3, "Testing the spec command")

        # Change to the test directory
        os.chdir(self.test_dir / "test_project")

        # Create a simple requirements file
        with open("requirements.md", "w") as f:
            f.write("# Test Requirements\n\n")
            f.write("1. The system shall provide a calculator function\n")
            f.write("2. The calculator shall support addition and subtraction\n")

        command = "devsynth spec --requirements-file requirements.md"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        # Check if the spec file was created
        spec_created = Path("./.devsynth/specs.md").exists()

        if spec_created:
            print("\nSpec file was created successfully.")
            # Show the content of the spec file
            with open("./.devsynth/specs.md") as f:
                print("\nContent of specs.md:")
                print(f.read())
        else:
            print("\nSpec file was NOT created.")

        result = self.get_user_input(
            "Did the spec command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("../..")

        self.record_result("Spec Command", command, result, notes)

    def test_test_command(self):
        """Test the test command."""
        self.print_step(4, "Testing the test command")

        # Change to the test directory
        os.chdir(self.test_dir / "test_project")

        command = "devsynth test"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        # Check if test files were created
        tests_created = Path("./tests").exists()

        if tests_created:
            print("\nTest files were created successfully.")
            # List the test files
            test_files = list(Path("./tests").glob("**/*.py"))
            print("\nTest files created:")
            for test_file in test_files:
                print(f"- {test_file}")
        else:
            print("\nTest files were NOT created.")

        result = self.get_user_input(
            "Did the test command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("../..")

        self.record_result("Test Command", command, result, notes)

    def test_code_command(self):
        """Test the code command."""
        self.print_step(5, "Testing the code command")

        # Change to the test directory
        os.chdir(self.test_dir / "test_project")

        command = "devsynth code"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        # Check if code files were created
        code_created = Path("./src").exists()

        if code_created:
            print("\nCode files were created successfully.")
            # List the code files
            code_files = list(Path("./src").glob("**/*.py"))
            print("\nCode files created:")
            for code_file in code_files:
                print(f"- {code_file}")
        else:
            print("\nCode files were NOT created.")

        result = self.get_user_input(
            "Did the code command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("../..")

        self.record_result("Code Command", command, result, notes)

    def test_run_command(self):
        """Test running the generated test suite."""
        self.print_step(6, "Testing the run command")

        # Change to the test directory
        os.chdir(self.test_dir / "test_project")

        print("Running unit tests...")
        success, output = run_tests("unit-tests")

        print("\nOutput:")
        print(output)

        result = self.get_user_input(
            "Did the run command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("../..")

        self.record_result("Run Command", "run_tests('unit-tests')", result, notes)

    def test_config_command(self):
        """Test the config command."""
        self.print_step(7, "Testing the config command")

        # Change to the test directory
        os.chdir(self.test_dir / "test_project")

        command = "devsynth config --key model --value gpt-4"
        print(f"Running command: {command}")

        returncode, stdout, stderr = self.run_command(command)

        print("\nOutput:")
        print(stdout)

        if stderr:
            print("\nErrors:")
            print(stderr)

        # Check if the config was updated
        config_updated = False
        config_file = Path("./.devsynth/config.json")

        if config_file.exists():
            import json

            try:
                with open(config_file) as f:
                    config = json.load(f)
                    if config.get("model") == "gpt-4":
                        config_updated = True
                        print("\nConfig was updated successfully.")
                        print(f"Current config: {config}")
            except Exception as e:
                print(f"\nError reading config file: {e}")

        if not config_updated:
            print("\nConfig was NOT updated.")

        result = self.get_user_input(
            "Did the config command work as expected?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        # Change back to the original directory
        os.chdir("../..")

        self.record_result("Config Command", command, result, notes)

    def run_all_tests(self):
        """Run all CLI workflow tests."""
        print("Starting DevSynth CLI Workflow Tests")
        print(f"Results will be saved to {self.output_file}")

        try:
            self.test_help_command()
            self.test_init_command()
            self.test_spec_command()
            self.test_test_command()
            self.test_code_command()
            self.test_run_command()
            self.test_config_command()

            # Additional tests can be added here

            self.save_results()
        finally:
            self.cleanup()


def main():
    """Main function to run the CLI workflow tester."""
    parser = argparse.ArgumentParser(description="Test DevSynth CLI workflows")
    parser.add_argument(
        "--output",
        default="cli_test_results.md",
        help="Output file for test results (default: cli_test_results.md)",
    )

    args = parser.parse_args()

    tester = CLIWorkflowTester(args.output)
    tester.run_all_tests()

    return 0


if __name__ == "__main__":
    sys.exit(main())

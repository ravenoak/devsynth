#!/usr/bin/env python3
"""
Script to guide manual testing of DevSynth WebUI navigation and functionality.

This script walks the user through testing various WebUI pages and workflows,
and records the results. It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/webui_testing.py [--output FILENAME]

Options:
    --output FILENAME    Output file for test results (default: webui_test_results.md)
"""

import argparse
import os
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path


class WebUITester:
    """Class to guide manual testing of WebUI navigation and functionality."""

    def __init__(self, output_file="webui_test_results.md"):
        """
        Initialize the tester.

        Args:
            output_file (str): Path to the output file for test results
        """
        self.output_file = output_file
        self.results = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.webui_process = None

    def start_webui(self):
        """Start the WebUI server."""
        print("Starting DevSynth WebUI server...")

        try:
            # Start the WebUI server in a separate process
            self.webui_process = subprocess.Popen(
                ["devsynth", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for the server to start
            time.sleep(5)

            # Check if the server started successfully
            if self.webui_process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.webui_process.communicate()
                print("Error starting WebUI server:")
                print(stderr)
                return False

            print("WebUI server started successfully.")
            return True
        except Exception as e:
            print(f"Error starting WebUI server: {e}")
            return False

    def stop_webui(self):
        """Stop the WebUI server."""
        if self.webui_process is not None:
            print("Stopping WebUI server...")
            self.webui_process.terminate()
            try:
                self.webui_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.webui_process.kill()
            print("WebUI server stopped.")

    def open_browser(self, url="http://localhost:8501"):
        """Open the browser to the specified URL."""
        print(f"Opening browser to {url}")
        webbrowser.open(url)

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

    def record_result(self, test_name, result, notes=""):
        """
        Record a test result.

        Args:
            test_name (str): Name of the test
            result (str): Result of the test (pass/fail)
            notes (str): Additional notes
        """
        self.results.append({"test_name": test_name, "result": result, "notes": notes})

    def save_results(self):
        """Save the test results to a file."""
        with open(self.output_file, "w") as f:
            f.write(f"# DevSynth WebUI Test Results\n\n")
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
                f.write(f"**Result:** {result['result'].upper()}\n\n")
                if result["notes"]:
                    f.write(f"**Notes:** {result['notes']}\n\n")
                f.write("---\n\n")

        print(f"\nTest results saved to {self.output_file}")

    def test_home_page(self):
        """Test the home page."""
        self.print_step(1, "Testing the home page")

        print("Please navigate to the home page (http://localhost:8501)")
        print("Verify that the following elements are present:")
        print("- DevSynth logo and header")
        print("- Navigation sidebar with links to different pages")
        print("- Welcome message and getting started information")

        result = self.get_user_input(
            "Does the home page display correctly with all expected elements?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Home Page", result, notes)

    def test_project_creation(self):
        """Test project creation functionality."""
        self.print_step(2, "Testing project creation")

        print("Please navigate to the 'New Project' page")
        print("Verify that you can:")
        print("1. Enter a project name")
        print("2. Select a project location")
        print("3. Choose project settings")
        print("4. Create a new project")

        result = self.get_user_input(
            "Were you able to create a new project successfully?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Project Creation", result, notes)

    def test_requirements_page(self):
        """Test the requirements page."""
        self.print_step(3, "Testing the requirements page")

        print("Please navigate to the 'Requirements' page for your project")
        print("Verify that you can:")
        print("1. View existing requirements")
        print("2. Add new requirements")
        print("3. Edit existing requirements")
        print("4. Save changes")

        result = self.get_user_input(
            "Does the requirements page function correctly?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Requirements Page", result, notes)

    def test_specifications_page(self):
        """Test the specifications page."""
        self.print_step(4, "Testing the specifications page")

        print("Please navigate to the 'Specifications' page for your project")
        print("Verify that you can:")
        print("1. View existing specifications")
        print("2. Generate specifications from requirements")
        print("3. Edit specifications")
        print("4. Save changes")

        result = self.get_user_input(
            "Does the specifications page function correctly?", options=["pass", "fail"]
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Specifications Page", result, notes)

    def test_test_generation_page(self):
        """Test the test generation page."""
        self.print_step(5, "Testing the test generation page")

        print("Please navigate to the 'Test Generation' page for your project")
        print("Verify that you can:")
        print("1. Generate tests from specifications")
        print("2. View generated tests")
        print("3. Edit tests")
        print("4. Save changes")

        result = self.get_user_input(
            "Does the test generation page function correctly?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Test Generation Page", result, notes)

    def test_code_generation_page(self):
        """Test the code generation page."""
        self.print_step(6, "Testing the code generation page")

        print("Please navigate to the 'Code Generation' page for your project")
        print("Verify that you can:")
        print("1. Generate code from tests")
        print("2. View generated code")
        print("3. Edit code")
        print("4. Save changes")

        result = self.get_user_input(
            "Does the code generation page function correctly?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Code Generation Page", result, notes)

    def test_project_settings_page(self):
        """Test the project settings page."""
        self.print_step(7, "Testing the project settings page")

        print("Please navigate to the 'Project Settings' page for your project")
        print("Verify that you can:")
        print("1. View project settings")
        print("2. Edit project settings")
        print("3. Save changes")

        result = self.get_user_input(
            "Does the project settings page function correctly?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Project Settings Page", result, notes)

    def test_navigation_flow(self):
        """Test the navigation flow between pages."""
        self.print_step(8, "Testing navigation flow between pages")

        print("Please test the navigation flow between pages:")
        print("1. Navigate from Home to Project List")
        print("2. Navigate from Project List to a specific Project")
        print("3. Navigate between different pages within a Project")
        print("4. Navigate back to Home")

        result = self.get_user_input(
            "Is the navigation flow between pages smooth and intuitive?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Navigation Flow", result, notes)

    def test_error_handling(self):
        """Test error handling in the WebUI."""
        self.print_step(9, "Testing error handling")

        print("Please test error handling in the WebUI:")
        print("1. Try to create a project with an invalid name")
        print("2. Try to generate specifications without requirements")
        print("3. Try to generate tests without specifications")
        print("4. Try to generate code without tests")

        result = self.get_user_input(
            "Does the WebUI handle errors gracefully with clear error messages?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Error Handling", result, notes)

    def test_responsive_design(self):
        """Test responsive design of the WebUI."""
        self.print_step(10, "Testing responsive design")

        print("Please test the responsive design of the WebUI:")
        print("1. Resize the browser window to different sizes")
        print(
            "2. Test on a mobile device or using browser developer tools to simulate different screen sizes"
        )

        result = self.get_user_input(
            "Does the WebUI adapt well to different screen sizes?",
            options=["pass", "fail"],
        )

        notes = self.get_user_input("Enter any notes about this test (optional)")

        self.record_result("Responsive Design", result, notes)

    def run_all_tests(self):
        """Run all WebUI tests."""
        print("Starting DevSynth WebUI Tests")
        print(f"Results will be saved to {self.output_file}")

        # Start the WebUI server
        if not self.start_webui():
            print("Failed to start WebUI server. Aborting tests.")
            return

        # Open the browser
        self.open_browser()

        try:
            # Run the tests
            self.test_home_page()
            self.test_project_creation()
            self.test_requirements_page()
            self.test_specifications_page()
            self.test_test_generation_page()
            self.test_code_generation_page()
            self.test_project_settings_page()
            self.test_navigation_flow()
            self.test_error_handling()
            self.test_responsive_design()

            # Save the results
            self.save_results()
        finally:
            # Stop the WebUI server
            self.stop_webui()


def main():
    """Main function to run the WebUI tester."""
    parser = argparse.ArgumentParser(
        description="Test DevSynth WebUI navigation and functionality"
    )
    parser.add_argument(
        "--output",
        default="webui_test_results.md",
        help="Output file for test results (default: webui_test_results.md)",
    )

    args = parser.parse_args()

    tester = WebUITester(args.output)
    tester.run_all_tests()

    return 0


if __name__ == "__main__":
    sys.exit(main())

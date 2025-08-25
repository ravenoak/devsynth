#!/usr/bin/env python3
"""
Script to test DevSynth with different configuration options.

This script tests DevSynth with various configuration settings and records the results.
It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/config_testing.py [--output FILENAME]

Options:
    --output FILENAME    Output file for test results (default: config_test_results.md)
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import yaml


class ConfigTester:
    """Class to test DevSynth with different configuration options."""

    def __init__(self, output_file="config_test_results.md"):
        """
        Initialize the tester.

        Args:
            output_file (str): Path to the output file for test results
        """
        self.output_file = output_file
        self.results = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")

        # Create a temporary directory for testing
        self.test_dir = Path(tempfile.mkdtemp())
        print(f"Created temporary directory: {self.test_dir}")

        # Save the original working directory
        self.original_dir = Path.cwd()

    def cleanup(self):
        """Clean up temporary files and directories."""
        os.chdir(self.original_dir)
        try:
            shutil.rmtree(self.test_dir)
            print(f"Cleaned up temporary directory: {self.test_dir}")
        except Exception as e:
            print(f"Error cleaning up temporary directory: {e}")

    def run_command(self, command, env=None):
        """
        Run a command and return the result.

        Args:
            command (str): Command to run
            env (dict): Environment variables to set

        Returns:
            tuple: (returncode, stdout, stderr)
        """
        try:
            process = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
                env=env,
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

    def record_result(self, test_name, config, command, returncode, stdout, stderr):
        """
        Record a test result.

        Args:
            test_name (str): Name of the test
            config (dict): Configuration that was tested
            command (str): Command that was run
            returncode (int): Return code from the command
            stdout (str): Standard output from the command
            stderr (str): Standard error from the command
        """
        result = "pass" if returncode == 0 else "fail"

        self.results.append(
            {
                "test_name": test_name,
                "config": config,
                "command": command,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "result": result,
            }
        )

    def save_results(self):
        """Save the test results to a file."""
        with open(self.output_file, "w") as f:
            f.write(f"# DevSynth Configuration Test Results\n\n")
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

                f.write("**Configuration:**\n\n")
                f.write("```yaml\n")
                f.write(yaml.dump(result["config"], default_flow_style=False))
                f.write("```\n\n")

                f.write(f"**Command:** `{result['command']}`\n\n")
                f.write(f"**Return Code:** {result['returncode']}\n\n")
                f.write(f"**Result:** {result['result'].upper()}\n\n")

                if result["stdout"]:
                    f.write("**Standard Output:**\n\n")
                    f.write("```\n")
                    f.write(result["stdout"])
                    f.write("```\n\n")

                if result["stderr"]:
                    f.write("**Standard Error:**\n\n")
                    f.write("```\n")
                    f.write(result["stderr"])
                    f.write("```\n\n")

                f.write("---\n\n")

        print(f"\nTest results saved to {self.output_file}")

    def create_project(self, project_name="test_project"):
        """
        Create a test project.

        Args:
            project_name (str): Name of the project

        Returns:
            Path: Path to the project directory
        """
        project_dir = self.test_dir / project_name

        # Create the project directory
        project_dir.mkdir(exist_ok=True)

        # Create the .devsynth directory
        devsynth_dir = project_dir / ".devsynth"
        devsynth_dir.mkdir(exist_ok=True)

        return project_dir

    def create_config_file(self, project_dir, config, format="yaml"):
        """
        Create a configuration file in the project directory.

        Args:
            project_dir (Path): Path to the project directory
            config (dict): Configuration to write
            format (str): Format of the configuration file (yaml or json)

        Returns:
            Path: Path to the configuration file
        """
        devsynth_dir = project_dir / ".devsynth"

        if format == "yaml":
            config_file = devsynth_dir / "project.yaml"
            with open(config_file, "w") as f:
                yaml.dump(config, f, default_flow_style=False)
        else:  # json
            config_file = devsynth_dir / "config.json"
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)

        return config_file

    def test_default_config(self):
        """Test with default configuration."""
        self.print_step(1, "Testing with default configuration")

        # Create a project with default configuration
        project_dir = self.create_project("default_config")
        os.chdir(project_dir)

        # Create a simple requirements file
        with open("requirements.md", "w") as f:
            f.write("# Test Requirements\n\n")
            f.write("1. The system shall provide a calculator function\n")
            f.write("2. The calculator shall support addition and subtraction\n")

        # Run the spec command
        command = "devsynth spec --requirements-file requirements.md"
        returncode, stdout, stderr = self.run_command(command)

        # Record the result
        self.record_result(
            "Default Configuration",
            {"model": "default"},
            command,
            returncode,
            stdout,
            stderr,
        )

    def test_different_models(self):
        """Test with different LLM models."""
        self.print_step(2, "Testing with different LLM models")

        models = ["gpt-4", "gpt-3.5-turbo", "claude-3-opus-20240229"]

        for model in models:
            # Create a project with the specified model
            project_dir = self.create_project(f"model_{model.replace('.', '_')}")
            config = {"model": model}
            self.create_config_file(project_dir, config)

            os.chdir(project_dir)

            # Create a simple requirements file
            with open("requirements.md", "w") as f:
                f.write("# Test Requirements\n\n")
                f.write("1. The system shall provide a calculator function\n")
                f.write("2. The calculator shall support addition and subtraction\n")

            # Run the spec command
            command = "devsynth spec --requirements-file requirements.md"
            returncode, stdout, stderr = self.run_command(command)

            # Record the result
            self.record_result(
                f"Model: {model}", config, command, returncode, stdout, stderr
            )

    def test_different_providers(self):
        """Test with different LLM providers."""
        self.print_step(3, "Testing with different LLM providers")

        providers = ["openai", "anthropic", "lmstudio"]

        for provider in providers:
            # Create a project with the specified provider
            project_dir = self.create_project(f"provider_{provider}")
            config = {"provider": provider}
            self.create_config_file(project_dir, config)

            os.chdir(project_dir)

            # Create a simple requirements file
            with open("requirements.md", "w") as f:
                f.write("# Test Requirements\n\n")
                f.write("1. The system shall provide a calculator function\n")
                f.write("2. The calculator shall support addition and subtraction\n")

            # Run the spec command
            command = "devsynth spec --requirements-file requirements.md"
            returncode, stdout, stderr = self.run_command(command)

            # Record the result
            self.record_result(
                f"Provider: {provider}", config, command, returncode, stdout, stderr
            )

    def test_different_memory_backends(self):
        """Test with different memory backends."""
        self.print_step(4, "Testing with different memory backends")

        memory_backends = ["simple", "chromadb", "faiss", "kuzu"]

        for backend in memory_backends:
            # Create a project with the specified memory backend
            project_dir = self.create_project(f"memory_{backend}")
            config = {"memory": {"backend": backend}}
            self.create_config_file(project_dir, config)

            os.chdir(project_dir)

            # Create a simple requirements file
            with open("requirements.md", "w") as f:
                f.write("# Test Requirements\n\n")
                f.write("1. The system shall provide a calculator function\n")
                f.write("2. The calculator shall support addition and subtraction\n")

            # Run the spec command
            command = "devsynth spec --requirements-file requirements.md"
            returncode, stdout, stderr = self.run_command(command)

            # Record the result
            self.record_result(
                f"Memory Backend: {backend}",
                config,
                command,
                returncode,
                stdout,
                stderr,
            )

    def test_different_languages(self):
        """Test with different programming languages."""
        self.print_step(5, "Testing with different programming languages")

        languages = ["python", "javascript", "java", "go", "rust"]

        for language in languages:
            # Create a project with the specified language
            project_dir = self.create_project(f"language_{language}")
            config = {"language": language}
            self.create_config_file(project_dir, config)

            os.chdir(project_dir)

            # Create a simple requirements file
            with open("requirements.md", "w") as f:
                f.write("# Test Requirements\n\n")
                f.write("1. The system shall provide a calculator function\n")
                f.write("2. The calculator shall support addition and subtraction\n")

            # Run the spec command
            command = "devsynth spec --requirements-file requirements.md"
            returncode, stdout, stderr = self.run_command(command)

            # Record the result
            self.record_result(
                f"Language: {language}", config, command, returncode, stdout, stderr
            )

    def test_different_architectures(self):
        """Test with different architecture styles."""
        self.print_step(6, "Testing with different architecture styles")

        architectures = ["hexagonal", "mvc", "clean", "microservices"]

        for architecture in architectures:
            # Create a project with the specified architecture
            project_dir = self.create_project(f"architecture_{architecture}")
            config = {"architecture": architecture}
            self.create_config_file(project_dir, config)

            os.chdir(project_dir)

            # Create a simple requirements file
            with open("requirements.md", "w") as f:
                f.write("# Test Requirements\n\n")
                f.write("1. The system shall provide a calculator function\n")
                f.write("2. The calculator shall support addition and subtraction\n")

            # Run the spec command
            command = "devsynth spec --requirements-file requirements.md"
            returncode, stdout, stderr = self.run_command(command)

            # Record the result
            self.record_result(
                f"Architecture: {architecture}",
                config,
                command,
                returncode,
                stdout,
                stderr,
            )

    def test_different_test_frameworks(self):
        """Test with different test frameworks."""
        self.print_step(7, "Testing with different test frameworks")

        test_frameworks = {
            "python": ["pytest", "unittest"],
            "javascript": ["jest", "mocha"],
            "java": ["junit", "testng"],
            "go": ["testing", "testify"],
            "rust": ["cargo-test"],
        }

        for language, frameworks in test_frameworks.items():
            for framework in frameworks:
                # Create a project with the specified test framework
                project_dir = self.create_project(
                    f"test_framework_{language}_{framework}"
                )
                config = {"language": language, "testing": {"framework": framework}}
                self.create_config_file(project_dir, config)

                os.chdir(project_dir)

                # Create a simple requirements file
                with open("requirements.md", "w") as f:
                    f.write("# Test Requirements\n\n")
                    f.write("1. The system shall provide a calculator function\n")
                    f.write(
                        "2. The calculator shall support addition and subtraction\n"
                    )

                # Run the test command
                command = "devsynth test"
                returncode, stdout, stderr = self.run_command(command)

                # Record the result
                self.record_result(
                    f"Test Framework: {language}/{framework}",
                    config,
                    command,
                    returncode,
                    stdout,
                    stderr,
                )

    def test_environment_variables(self):
        """Test with environment variables."""
        self.print_step(8, "Testing with environment variables")

        # Create a project
        project_dir = self.create_project("env_vars")
        os.chdir(project_dir)

        # Create a simple requirements file
        with open("requirements.md", "w") as f:
            f.write("# Test Requirements\n\n")
            f.write("1. The system shall provide a calculator function\n")
            f.write("2. The calculator shall support addition and subtraction\n")

        # Run the spec command with environment variables
        env = os.environ.copy()
        env["DEVSYNTH_MODEL"] = "gpt-4"
        env["DEVSYNTH_PROVIDER"] = "openai"
        env["DEVSYNTH_LANGUAGE"] = "python"

        command = "devsynth spec --requirements-file requirements.md"
        returncode, stdout, stderr = self.run_command(command, env)

        # Record the result
        self.record_result(
            "Environment Variables",
            {
                "model": "gpt-4 (from env)",
                "provider": "openai (from env)",
                "language": "python (from env)",
            },
            command,
            returncode,
            stdout,
            stderr,
        )

    def test_command_line_options(self):
        """Test with command line options."""
        self.print_step(9, "Testing with command line options")

        # Create a project
        project_dir = self.create_project("cmd_options")
        os.chdir(project_dir)

        # Create a simple requirements file
        with open("requirements.md", "w") as f:
            f.write("# Test Requirements\n\n")
            f.write("1. The system shall provide a calculator function\n")
            f.write("2. The calculator shall support addition and subtraction\n")

        # Run the spec command with command line options
        command = "devsynth spec --requirements-file requirements.md --model gpt-4 --provider openai --language python"
        returncode, stdout, stderr = self.run_command(command)

        # Record the result
        self.record_result(
            "Command Line Options",
            {
                "model": "gpt-4 (from cmd)",
                "provider": "openai (from cmd)",
                "language": "python (from cmd)",
            },
            command,
            returncode,
            stdout,
            stderr,
        )

    def test_complex_configuration(self):
        """Test with a complex configuration."""
        self.print_step(10, "Testing with a complex configuration")

        # Create a project with a complex configuration
        project_dir = self.create_project("complex_config")

        config = {
            "model": "gpt-4",
            "provider": "openai",
            "language": "python",
            "architecture": "hexagonal",
            "memory": {
                "backend": "chromadb",
                "path": ".devsynth/memory",
                "collection": "test_collection",
            },
            "testing": {"framework": "pytest", "coverage": True, "behavior": True},
            "logging": {"level": "info", "file": ".devsynth/logs/devsynth.log"},
            "features": {
                "auto_tuning": True,
                "code_analysis": True,
                "dialectical_reasoning": True,
            },
        }

        self.create_config_file(project_dir, config)

        os.chdir(project_dir)

        # Create a simple requirements file
        with open("requirements.md", "w") as f:
            f.write("# Test Requirements\n\n")
            f.write("1. The system shall provide a calculator function\n")
            f.write("2. The calculator shall support addition and subtraction\n")

        # Run the spec command
        command = "devsynth spec --requirements-file requirements.md"
        returncode, stdout, stderr = self.run_command(command)

        # Record the result
        self.record_result(
            "Complex Configuration", config, command, returncode, stdout, stderr
        )

    def run_all_tests(self):
        """Run all configuration tests."""
        print("Starting DevSynth Configuration Tests")
        print(f"Results will be saved to {self.output_file}")

        try:
            self.test_default_config()
            self.test_different_models()
            self.test_different_providers()
            self.test_different_memory_backends()
            self.test_different_languages()
            self.test_different_architectures()
            self.test_different_test_frameworks()
            self.test_environment_variables()
            self.test_command_line_options()
            self.test_complex_configuration()

            self.save_results()
        finally:
            self.cleanup()


def main():
    """Main function to run the configuration tester."""
    parser = argparse.ArgumentParser(
        description="Test DevSynth with different configuration options"
    )
    parser.add_argument(
        "--output",
        default="config_test_results.md",
        help="Output file for test results (default: config_test_results.md)",
    )

    args = parser.parse_args()

    tester = ConfigTester(args.output)
    tester.run_all_tests()

    return 0


if __name__ == "__main__":
    sys.exit(main())

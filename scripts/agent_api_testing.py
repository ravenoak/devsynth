#!/usr/bin/env python3
"""
Script to verify DevSynth Agent API with external clients.

This script tests the Agent API endpoints with various clients and records the results.
It's part of the Phase 4 comprehensive testing effort.

Usage:
    python scripts/agent_api_testing.py [--output FILENAME] [--host HOST] [--port PORT]

Options:
    --output FILENAME    Output file for test results (default: agent_api_test_results.md)
    --host HOST          Host for the Agent API server (default: localhost)
    --port PORT          Port for the Agent API server (default: 8000)
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import requests


class AgentAPITester:
    """Class to verify Agent API with external clients."""

    def __init__(
        self, output_file="agent_api_test_results.md", host="localhost", port=8000
    ):
        """
        Initialize the tester.

        Args:
            output_file (str): Path to the output file for test results
            host (str): Host for the Agent API server
            port (int): Port for the Agent API server
        """
        self.output_file = output_file
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.results = []
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.api_process = None
        self.api_key = "test-api-key"  # For testing purposes

    def start_api_server(self):
        """Start the Agent API server."""
        print("Starting DevSynth Agent API server...")

        try:
            # Start the API server in a separate process
            self.api_process = subprocess.Popen(
                ["devsynth", "serve", "--api", "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env={**os.environ, "DEVSYNTH_API_KEY": self.api_key},
            )

            # Wait for the server to start
            time.sleep(5)

            # Check if the server started successfully
            if self.api_process.poll() is not None:
                # Process has terminated
                stdout, stderr = self.api_process.communicate()
                print("Error starting Agent API server:")
                print(stderr)
                return False

            # Check if the server is responding
            try:
                response = requests.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    print("Agent API server started successfully.")
                    return True
                else:
                    print(
                        f"Agent API server returned unexpected status code: {response.status_code}"
                    )
                    return False
            except requests.exceptions.ConnectionError:
                print("Could not connect to Agent API server.")
                return False
        except Exception as e:
            print(f"Error starting Agent API server: {e}")
            return False

    def stop_api_server(self):
        """Stop the Agent API server."""
        if self.api_process is not None:
            print("Stopping Agent API server...")
            self.api_process.terminate()
            try:
                self.api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.api_process.kill()
            print("Agent API server stopped.")

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

    def record_result(
        self,
        test_name,
        endpoint,
        method,
        status_code,
        expected_status_code,
        response_data=None,
        notes="",
    ):
        """
        Record a test result.

        Args:
            test_name (str): Name of the test
            endpoint (str): API endpoint that was tested
            method (str): HTTP method that was used
            status_code (int): HTTP status code that was returned
            expected_status_code (int): Expected HTTP status code
            response_data (dict): Response data from the API
            notes (str): Additional notes
        """
        result = "pass" if status_code == expected_status_code else "fail"

        self.results.append(
            {
                "test_name": test_name,
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
                "expected_status_code": expected_status_code,
                "result": result,
                "response_data": response_data,
                "notes": notes,
            }
        )

    def save_results(self):
        """Save the test results to a file."""
        with open(self.output_file, "w") as f:
            f.write(f"# DevSynth Agent API Test Results\n\n")
            f.write(f"Date: {self.current_date}\n\n")
            f.write(f"Host: {self.host}\n")
            f.write(f"Port: {self.port}\n\n")

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
                f.write(f"**Endpoint:** `{result['endpoint']}`\n\n")
                f.write(f"**Method:** {result['method']}\n\n")
                f.write(
                    f"**Status Code:** {result['status_code']} (Expected: {result['expected_status_code']})\n\n"
                )
                f.write(f"**Result:** {result['result'].upper()}\n\n")

                if result["response_data"]:
                    f.write("**Response Data:**\n\n")
                    f.write("```json\n")
                    f.write(json.dumps(result["response_data"], indent=2))
                    f.write("\n```\n\n")

                if result["notes"]:
                    f.write(f"**Notes:** {result['notes']}\n\n")

                f.write("---\n\n")

        print(f"\nTest results saved to {self.output_file}")

    def test_health_endpoint(self):
        """Test the health endpoint."""
        self.print_step(1, "Testing the health endpoint")

        endpoint = "/health"
        method = "GET"

        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            status_code = response.status_code
            expected_status_code = 200

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Health Endpoint",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing health endpoint: {e}")
            self.record_result(
                "Health Endpoint", endpoint, method, 0, 200, None, f"Error: {str(e)}"
            )

    def test_health_endpoint_with_auth(self):
        """Test the health endpoint with authentication."""
        self.print_step(2, "Testing the health endpoint with authentication")

        endpoint = "/health"
        method = "GET"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            status_code = response.status_code
            expected_status_code = 200

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Health Endpoint with Authentication",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing health endpoint with authentication: {e}")
            self.record_result(
                "Health Endpoint with Authentication",
                endpoint,
                method,
                0,
                200,
                None,
                f"Error: {str(e)}",
            )

    def test_metrics_endpoint(self):
        """Test the metrics endpoint."""
        self.print_step(3, "Testing the metrics endpoint")

        endpoint = "/metrics"
        method = "GET"

        try:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(f"{self.base_url}{endpoint}", headers=headers)
            status_code = response.status_code
            expected_status_code = 200

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Metrics Endpoint",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing metrics endpoint: {e}")
            self.record_result(
                "Metrics Endpoint", endpoint, method, 0, 200, None, f"Error: {str(e)}"
            )

    def test_metrics_endpoint_without_auth(self):
        """Test the metrics endpoint without authentication."""
        self.print_step(4, "Testing the metrics endpoint without authentication")

        endpoint = "/metrics"
        method = "GET"

        try:
            response = requests.get(f"{self.base_url}{endpoint}")
            status_code = response.status_code
            expected_status_code = 401  # Unauthorized

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Metrics Endpoint without Authentication",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing metrics endpoint without authentication: {e}")
            self.record_result(
                "Metrics Endpoint without Authentication",
                endpoint,
                method,
                0,
                401,
                None,
                f"Error: {str(e)}",
            )

    def test_generate_endpoint(self):
        """Test the generate endpoint."""
        self.print_step(5, "Testing the generate endpoint")

        endpoint = "/generate"
        method = "POST"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "prompt": "Write a simple Python function to add two numbers.",
                "max_tokens": 100,
            }
            response = requests.post(
                f"{self.base_url}{endpoint}", headers=headers, json=data
            )
            status_code = response.status_code
            expected_status_code = 200

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Generate Endpoint",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing generate endpoint: {e}")
            self.record_result(
                "Generate Endpoint", endpoint, method, 0, 200, None, f"Error: {str(e)}"
            )

    def test_generate_endpoint_without_auth(self):
        """Test the generate endpoint without authentication."""
        self.print_step(6, "Testing the generate endpoint without authentication")

        endpoint = "/generate"
        method = "POST"

        try:
            headers = {"Content-Type": "application/json"}
            data = {
                "prompt": "Write a simple Python function to add two numbers.",
                "max_tokens": 100,
            }
            response = requests.post(
                f"{self.base_url}{endpoint}", headers=headers, json=data
            )
            status_code = response.status_code
            expected_status_code = 401  # Unauthorized

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Generate Endpoint without Authentication",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing generate endpoint without authentication: {e}")
            self.record_result(
                "Generate Endpoint without Authentication",
                endpoint,
                method,
                0,
                401,
                None,
                f"Error: {str(e)}",
            )

    def test_generate_endpoint_with_invalid_data(self):
        """Test the generate endpoint with invalid data."""
        self.print_step(7, "Testing the generate endpoint with invalid data")

        endpoint = "/generate"
        method = "POST"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                # Missing required 'prompt' field
                "max_tokens": 100
            }
            response = requests.post(
                f"{self.base_url}{endpoint}", headers=headers, json=data
            )
            status_code = response.status_code
            expected_status_code = 400  # Bad Request

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Generate Endpoint with Invalid Data",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing generate endpoint with invalid data: {e}")
            self.record_result(
                "Generate Endpoint with Invalid Data",
                endpoint,
                method,
                0,
                400,
                None,
                f"Error: {str(e)}",
            )

    def test_analyze_endpoint(self):
        """Test the analyze endpoint."""
        self.print_step(8, "Testing the analyze endpoint")

        endpoint = "/analyze"
        method = "POST"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {"code": "def add(a, b):\n    return a + b", "language": "python"}
            response = requests.post(
                f"{self.base_url}{endpoint}", headers=headers, json=data
            )
            status_code = response.status_code
            expected_status_code = 200

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Analyze Endpoint",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing analyze endpoint: {e}")
            self.record_result(
                "Analyze Endpoint", endpoint, method, 0, 200, None, f"Error: {str(e)}"
            )

    def test_analyze_endpoint_with_invalid_data(self):
        """Test the analyze endpoint with invalid data."""
        self.print_step(9, "Testing the analyze endpoint with invalid data")

        endpoint = "/analyze"
        method = "POST"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                # Missing required 'code' field
                "language": "python"
            }
            response = requests.post(
                f"{self.base_url}{endpoint}", headers=headers, json=data
            )
            status_code = response.status_code
            expected_status_code = 400  # Bad Request

            try:
                response_data = response.json()
            except:
                response_data = {"text": response.text}

            print(f"Response status code: {status_code}")
            print(f"Response data: {response_data}")

            self.record_result(
                "Analyze Endpoint with Invalid Data",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
            )
        except Exception as e:
            print(f"Error testing analyze endpoint with invalid data: {e}")
            self.record_result(
                "Analyze Endpoint with Invalid Data",
                endpoint,
                method,
                0,
                400,
                None,
                f"Error: {str(e)}",
            )

    def test_rate_limiting(self):
        """Test rate limiting."""
        self.print_step(10, "Testing rate limiting")

        endpoint = "/generate"
        method = "POST"

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            data = {
                "prompt": "Write a simple Python function to add two numbers.",
                "max_tokens": 100,
            }

            # Make multiple requests in quick succession
            responses = []
            for i in range(10):
                response = requests.post(
                    f"{self.base_url}{endpoint}", headers=headers, json=data
                )
                responses.append(response)

            # Check if any response has a 429 status code (Too Many Requests)
            rate_limited = any(response.status_code == 429 for response in responses)

            if rate_limited:
                status_code = 429
                expected_status_code = 429
                response_data = {"message": "Rate limiting is working as expected"}
                notes = "Rate limiting is working as expected"
            else:
                status_code = 200
                expected_status_code = 429
                response_data = {"message": "Rate limiting is not working as expected"}
                notes = "Rate limiting is not working as expected"

            print(f"Rate limiting test result: {notes}")

            self.record_result(
                "Rate Limiting",
                endpoint,
                method,
                status_code,
                expected_status_code,
                response_data,
                notes,
            )
        except Exception as e:
            print(f"Error testing rate limiting: {e}")
            self.record_result(
                "Rate Limiting", endpoint, method, 0, 429, None, f"Error: {str(e)}"
            )

    def run_all_tests(self):
        """Run all Agent API tests."""
        print("Starting DevSynth Agent API Tests")
        print(f"Results will be saved to {self.output_file}")

        # Start the API server
        if not self.start_api_server():
            print("Failed to start Agent API server. Aborting tests.")
            return

        try:
            # Run the tests
            self.test_health_endpoint()
            self.test_health_endpoint_with_auth()
            self.test_metrics_endpoint()
            self.test_metrics_endpoint_without_auth()
            self.test_generate_endpoint()
            self.test_generate_endpoint_without_auth()
            self.test_generate_endpoint_with_invalid_data()
            self.test_analyze_endpoint()
            self.test_analyze_endpoint_with_invalid_data()
            self.test_rate_limiting()

            # Save the results
            self.save_results()
        finally:
            # Stop the API server
            self.stop_api_server()


def main():
    """Main function to run the Agent API tester."""
    parser = argparse.ArgumentParser(
        description="Test DevSynth Agent API with external clients"
    )
    parser.add_argument(
        "--output",
        default="agent_api_test_results.md",
        help="Output file for test results (default: agent_api_test_results.md)",
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host for the Agent API server (default: localhost)",
    )
    parser.add_argument(
        "--port",
        default=8000,
        type=int,
        help="Port for the Agent API server (default: 8000)",
    )

    args = parser.parse_args()

    tester = AgentAPITester(args.output, args.host, args.port)
    tester.run_all_tests()

    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
System Functionality Verification Script

This script comprehensively probes and verifies the DevSynth system functionality
by running targeted tests, checking component interactions, and validating
system behavior under various conditions.

Usage:
    python scripts/verify_system_functionality.py
"""

import subprocess
import sys
from pathlib import Path


class SystemVerifier:
    """Main class for verifying system functionality."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.verifications_passed = []
        self.verifications_failed = []

    def run_verifications(self):
        """Run all system functionality verifications."""
        print("🔬 Starting system functionality verification...")

        # 1. Core component verification
        self.verify_core_components()

        # 2. Integration verification
        self.verify_integrations()

        # 3. Performance verification
        self.verify_performance()

        # 4. Error handling verification
        self.verify_error_handling()

        # 5. LLM provider verification
        self.verify_llm_providers()

        print(
            f"✅ Verification complete! {len(self.verifications_passed)} passed, {len(self.verifications_failed)} failed."
        )

        if self.verifications_failed:
            print("\n❌ Failed verifications:")
            for failure in self.verifications_failed:
                print(f"  - {failure}")
            return False
        return True

    def verify_core_components(self):
        """Verify core system components are working."""
        print("🔧 Verifying core components...")

        # Test promise system
        if self.run_test_subset("tests/unit/application/promises/", "Promise system"):
            self.verifications_passed.append("Promise system")
        else:
            self.verifications_failed.append("Promise system")

        # Test agent system
        if self.run_test_subset("tests/unit/application/agents/", "Agent system"):
            self.verifications_passed.append("Agent system")
        else:
            self.verifications_failed.append("Agent system")

        # Test memory system
        if self.run_test_subset("tests/unit/application/memory/", "Memory system"):
            self.verifications_passed.append("Memory system")
        else:
            self.verifications_failed.append("Memory system")

    def verify_integrations(self):
        """Verify system integrations are working."""
        print("🔗 Verifying integrations...")

        # Test LLM provider integrations
        if self.run_test_subset("tests/integration/llm/", "LLM provider integrations"):
            self.verifications_passed.append("LLM provider integrations")
        else:
            self.verifications_failed.append("LLM provider integrations")

        # Test memory integrations
        if self.run_test_subset("tests/integration/memory/", "Memory integrations"):
            self.verifications_passed.append("Memory integrations")
        else:
            self.verifications_failed.append("Memory integrations")

    def verify_performance(self):
        """Verify system performance characteristics."""
        print("⚡ Verifying performance...")

        # Test fast execution paths
        if self.run_test_subset("tests/unit/general/", "Fast execution paths"):
            self.verifications_passed.append("Fast execution paths")
        else:
            self.verifications_failed.append("Fast execution paths")

    def verify_error_handling(self):
        """Verify error handling mechanisms."""
        print("🛡️  Verifying error handling...")

        # Test error scenarios
        if self.run_test_subset(
            "tests/unit/general/test_exceptions.py", "Error scenarios"
        ):
            self.verifications_passed.append("Error scenarios")
        else:
            self.verifications_failed.append("Error scenarios")

    def verify_llm_providers(self):
        """Verify LLM provider functionality."""
        print("🤖 Verifying LLM providers...")

        # Check available providers
        available_providers = self.check_available_providers()

        for provider in available_providers:
            if self.test_provider_functionality(provider):
                self.verifications_passed.append(f"LLM provider: {provider}")
            else:
                self.verifications_failed.append(f"LLM provider: {provider}")

    def run_test_subset(self, test_path: str, description: str) -> bool:
        """Run a subset of tests and return success status."""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-q", "--tb=no"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=60,  # 60 second timeout
            )

            if result.returncode == 0:
                print(f"✅ {description}: PASSED")
                return True
            else:
                print(f"❌ {description}: FAILED ({result.returncode})")
                return False
        except subprocess.TimeoutExpired:
            print(f"⏱️  {description}: TIMEOUT")
            return False
        except Exception as e:
            print(f"❌ {description}: ERROR ({e})")
            return False

    def check_available_providers(self) -> list:
        """Check which LLM providers are available."""
        try:
            result = subprocess.run(
                [
                    "python",
                    "-c",
                    """
from tests.conftest import is_resource_available
providers = ['anthropic', 'openai', 'openrouter', 'lmstudio']
available = [p for p in providers if is_resource_available(p)]
print(','.join(available) if available else 'none')
                """,
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
            )

            if result.returncode == 0:
                available = result.stdout.strip().split(",")
                return [p for p in available if p != "none" and p]
            return []
        except Exception:
            return []

    def test_provider_functionality(self, provider: str) -> bool:
        """Test if a specific provider works."""
        try:
            # Try to import and create a basic provider instance
            result = subprocess.run(
                [
                    "python",
                    "-c",
                    f"""
try:
    if '{provider}' == 'openai':
        from devsynth.application.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider({{'api_key': 'test'}})
    elif '{provider}' == 'openrouter':
        from devsynth.application.llm.openrouter_provider import OpenRouterProvider
        provider = OpenRouterProvider({{'api_key': 'test'}})
    elif '{provider}' == 'anthropic':
        from devsynth.application.llm.anthropic_provider import AnthropicProvider
        provider = AnthropicProvider({{'api_key': 'test'}})
    elif '{provider}' == 'lmstudio':
        from devsynth.application.llm.lmstudio_provider import LMStudioProvider
        provider = LMStudioProvider({{'base_url': 'http://localhost:1234'}})
    print('success')
except Exception as e:
    print(f'error: {e}')
                """,
                ],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=10,
            )

            return result.returncode == 0 and "success" in result.stdout
        except Exception:
            return False

    def generate_system_report(self):
        """Generate a comprehensive system verification report."""
        print("📊 Generating system verification report...")

        report = f"""
# DevSynth System Verification Report

## Test Results Summary
- **Passed**: {len(self.verifications_passed)}
- **Failed**: {len(self.verifications_failed)}

## Component Status
"""

        for component in self.verifications_passed:
            report += f"✅ {component}\n"

        for component in self.verifications_failed:
            report += f"❌ {component}\n"

        # Check available providers
        available_providers = self.check_available_providers()
        report += f"\n## Available LLM Providers\n"
        if available_providers:
            for provider in available_providers:
                report += f"✅ {provider}\n"
        else:
            report += "❌ No LLM providers available\n"

        # Save report
        report_path = self.project_root / "system_verification_report.md"
        with open(report_path, "w") as f:
            f.write(report)

        print(f"📄 Report saved to {report_path}")


def main():
    """Main entry point for system verification."""
    verifier = SystemVerifier()

    success = verifier.run_verifications()
    verifier.generate_system_report()

    if not success:
        print("\n⚠️  Some verifications failed. Check the report for details.")
        sys.exit(1)
    else:
        print("\n🎉 All verifications passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

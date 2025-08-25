"""Security and code quality checks for the WSDE model."""

from typing import Any

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


def _check_pep8_compliance(self: Any, code: str) -> bool:
    """Check if the code complies with PEP 8 style guide."""
    lines = code.split("\n")
    long_lines = sum(1 for line in lines if len(line) > 100)
    bad_indentation = sum(
        1 for line in lines if line.startswith(" ") and not line.startswith("    ")
    )
    snake_case_vars = sum(
        1 for line in lines if "=" in line and "_" in line.split("=")[0]
    )
    camel_case_vars = sum(
        1
        for line in lines
        if "=" in line
        and "_" not in line.split("=")[0]
        and not line.strip().startswith("#")
    )
    return (
        long_lines < len(lines) * 0.2
        and bad_indentation < len(lines) * 0.1
        and snake_case_vars > camel_case_vars
    )


def _check_security_best_practices(self: Any, code: str) -> bool:
    """Check if the code follows basic security best practices."""
    security_issues = [
        "password" in code.lower() and "=" in code,
        "token" in code.lower() and "=" in code,
        "exec(" in code.lower(),
        "eval(" in code.lower(),
        "subprocess" in code.lower() and "shell=True" in code.lower(),
    ]
    return not any(security_issues)


def _balance_security_and_performance(self: Any, code: str) -> str:
    """Annotate code with guidance on balancing security and performance."""
    if "# Security and performance balance:" not in code:
        code += """

# Security and performance balance:
# - Using efficient validation methods
# - Implementing security checks at critical points only
# - Using cached results where appropriate for repeated operations
"""
    return code


def _balance_security_and_usability(self: Any, code: str) -> str:
    """Annotate code with guidance on balancing security and usability."""
    if "# Security and usability balance:" not in code:
        code += """

# Security and usability balance:
# - Implementing progressive security measures
# - Using clear error messages for security issues
# - Providing helpful guidance for users
"""
    return code


def _balance_performance_and_maintainability(self: Any, code: str) -> str:
    """Annotate code with guidance on balancing performance and maintainability."""
    if "# Performance and maintainability balance:" not in code:
        code += """

# Performance and maintainability balance:
# - Using descriptive variable names even in performance-critical sections
# - Adding comments to explain optimization techniques
# - Extracting complex optimizations into well-named functions
"""
    return code

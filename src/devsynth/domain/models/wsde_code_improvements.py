"""Utility functions for improving code and documentation in WSDE."""
from typing import Any
from devsynth.logging_setup import DevSynthLogger
import re

logger = DevSynthLogger(__name__)


def _improve_credentials(self: Any, code: str) -> str:
    """Improve code by removing hardcoded credentials."""
    code = code.replace(
        "username == 'admin' and password == 'password'",
        "validate_credentials(username, password)",
    )
    if "def validate_credentials" not in code:
        code = (
            "def validate_credentials(username, password):\n"
            "    # Securely validate credentials against database\n"
            "    # In a real implementation, this would use a secure password hashing algorithm\n"
            "    # and compare against stored hashed passwords\n"
            "    return False  # Placeholder\n\n"
        ) + code
    return code


def _improve_error_handling(self: Any, code: str) -> str:
    """Improve code by adding error handling."""
    for func_name in ["authenticate", "process", "validate", "execute", "run"]:
        if f"def {func_name}" in code and "try:" not in code:
            code = code.replace(
                f"def {func_name}(",
                f"def {func_name}(",
            )
            pattern = rf"def {func_name}\([^)]*\):(.*?)(?=\ndef|\Z)"
            match = re.search(pattern, code, re.DOTALL)
            if match:
                func_body = match.group(1)
                indented_body = "\n    try:" + func_body.replace("\n", "\n    ")
                exception_handler = (
                    "\n    except Exception as e:\n        logger.error(f'{func_name} error: {e}')\n        return None"
                )
                new_body = indented_body + exception_handler
                code = code.replace(func_body, new_body)
    return code


def _improve_input_validation(self: Any, code: str) -> str:
    """Improve code by adding input validation."""
    for func_name in ["authenticate", "process", "validate", "execute", "run"]:
        if f"def {func_name}" in code and "if not " not in code:
            pattern = rf"def {func_name}\(([^)]*)\):"
            match = re.search(pattern, code)
            if match:
                params = match.group(1).split(",")
                param_names = [
                    p.strip().split(":")[0].split("=")[0].strip()
                    for p in params
                    if p.strip()
                ]
                validation_code = "\n    # Validate inputs\n"
                for param in param_names:
                    if param != "self":
                        validation_code += f"    if {param} is None:\n        return None\n"
                code = code.replace(
                    f"def {func_name}({match.group(1)}):",
                    f"def {func_name}({match.group(1)}):{validation_code}",
                )
    return code


def _improve_security(self: Any, code: str) -> str:
    """Improve code security."""
    replacements = {
        "eval(": "safe_eval(",
        "exec(": "safe_exec(",
        "os.system(": "subprocess.run([",
        "subprocess.call(": "subprocess.run(",
        "pickle.loads(": "safe_deserialize(",
    }
    for old, new in replacements.items():
        if old in code:
            code = code.replace(old, new)
            if new == "safe_eval(" and "def safe_eval" not in code:
                code = (
                    "def safe_eval(expr, globals=None, locals=None):\n"
                    "    # A safer version of eval that restricts the available functions\n"
                    "    # In a real implementation, this would use a proper sandboxing solution\n"
                    "    safe_globals = {'__builtins__': {}}\n"
                    "    if globals:\n"
                    "        safe_globals.update({k: v for k, v in globals.items() if k in ['math', 'datetime']})\n"
                    "    return eval(expr, safe_globals, locals)\n\n"
                ) + code
            if new == "safe_deserialize(" and "def safe_deserialize" not in code:
                code = (
                    "def safe_deserialize(data):\n"
                    "    # A safer version of pickle.loads\n"
                    "    # In a real implementation, this would use a safer serialization format like JSON\n"
                    "    import pickle\n"
                    "    return pickle.loads(data)\n\n"
                ) + code
    return code


def _improve_performance(self: Any, code: str) -> str:
    """Improve code performance."""
    if "def calculate" in code and "@lru_cache" not in code:
        code = "from functools import lru_cache\n\n" + code
        code = code.replace(
            "def calculate",
            "@lru_cache(maxsize=128)\ndef calculate",
        )
    return code


def _improve_readability(self: Any, code: str) -> str:
    """Improve code readability."""
    functions = re.finditer(r"def ([a-zA-Z0-9_]+)\(([^)]*)\):", code)
    for match in functions:
        func_name = match.group(1)
        params = match.group(2)
        func_pos = match.start()
        next_lines = code[func_pos : func_pos + 200].split("\n")
        has_docstring = False
        for line in next_lines[1:3]:
            if '"""' in line or "'''" in line:
                has_docstring = True
                break
        if not has_docstring:
            docstring = (
                f"\n    \"\"\"\n    {func_name.replace('_', ' ').title()}.\n    \"\"\"\n"
            )
            code = code.replace(
                f"def {func_name}({params}):",
                f"def {func_name}({params}):{docstring}",
            )
    return code


def _improve_clarity(self: Any, content: str) -> str:
    """Improve content clarity."""
    if not content:
        return content
    if not content.startswith("# ") and not content.startswith("## "):
        content = (
            "# Introduction\n\nThis document provides information about the system.\n\n"
            + content
        )
    if "conclusion" not in content.lower():
        content += "\n\n# Conclusion\n\nThis concludes the document."
    return content


def _improve_with_examples(self: Any, content: str) -> str:
    """Improve content by adding examples."""
    if not content:
        return content
    if "example" not in content.lower():
        content += (
            "\n\n# Examples\n\nHere are some examples to illustrate the concepts:\n\n"
            "1. Example 1: Basic usage\n2. Example 2: Advanced usage"
        )
    return content


def _improve_structure(self: Any, content: str) -> str:
    """Improve content structure."""
    if not content:
        return content
    if "table of contents" not in content.lower():
        headings = re.findall(r"^#+ (.+)$", content, re.MULTILINE)
        if headings:
            toc = "# Table of Contents\n\n"
            for i, heading in enumerate(headings):
                toc += f"{i+1}. {heading}\n"
            content = toc + "\n\n" + content
    return content

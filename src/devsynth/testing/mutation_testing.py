"""
Mutation Testing Framework for DevSynth

This module implements AST-based mutation testing to assess test quality by
introducing small changes (mutations) to the code and verifying that tests
catch these changes.

Mutation testing helps identify:
- Weak or missing test cases
- Code that is not effectively tested
- Areas where test coverage is misleading

Usage:
    from devsynth.testing.mutation_testing import MutationTester

    tester = MutationTester()
    results = tester.run_mutations('src/devsynth/core/', 'tests/unit/core/')
    print(f"Mutation score: {results.mutation_score:.2f}")
"""

from __future__ import annotations

import ast
import copy
import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict, Union
from collections.abc import Iterator

from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class MutationResult:
    """Result of a single mutation test."""

    mutation_id: str
    file_path: str
    line_number: int
    original_code: str
    mutated_code: str
    mutation_type: str
    killed: bool  # True if tests failed (mutation was caught)
    test_output: str
    execution_time: float
    error: str | None = None


class MutationTypeStats(TypedDict):
    total: int
    killed: int


class MutationSummary(TypedDict):
    mutation_types: dict[str, MutationTypeStats]
    file_breakdown: dict[str, MutationTypeStats]
    slowest_mutations: list[MutationResult]


@dataclass
class MutationReport:
    """Complete mutation testing report."""

    target_path: str
    test_path: str
    total_mutations: int
    killed_mutations: int
    survived_mutations: int
    mutation_score: float
    execution_time: float
    mutations: list[MutationResult]
    summary: MutationSummary


class MutationOperator:
    """Base class for mutation operators."""

    def __init__(self, name: str) -> None:
        self.name = name

    def can_mutate(self, node: ast.AST) -> bool:
        """Check if this operator can mutate the given node."""
        raise NotImplementedError

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        """Generate mutations for the given node."""
        raise NotImplementedError


class ArithmeticOperatorMutator(MutationOperator):
    """Mutates arithmetic operators (+, -, *, /, etc.)."""

    def __init__(self) -> None:
        super().__init__("arithmetic")
        self.mutations = {
            ast.Add: [ast.Sub, ast.Mult],
            ast.Sub: [ast.Add, ast.Mult],
            ast.Mult: [ast.Add, ast.Sub, ast.Div],
            ast.Div: [ast.Mult, ast.Sub],
            ast.Mod: [ast.Mult, ast.Div],
            ast.Pow: [ast.Mult, ast.Div],
        }

    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.BinOp) and type(node.op) in self.mutations

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.BinOp):
            for new_op_class in self.mutations.get(type(node.op), []):
                mutated = copy.deepcopy(node)
                mutated.op = new_op_class()
                yield mutated


class ComparisonOperatorMutator(MutationOperator):
    """Mutates comparison operators (==, !=, <, >, etc.)."""

    def __init__(self) -> None:
        super().__init__("comparison")
        self.mutations = {
            ast.Eq: [ast.NotEq, ast.Lt, ast.Gt],
            ast.NotEq: [ast.Eq, ast.Lt, ast.Gt],
            ast.Lt: [ast.LtE, ast.Gt, ast.GtE],
            ast.LtE: [ast.Lt, ast.Gt, ast.GtE],
            ast.Gt: [ast.GtE, ast.Lt, ast.LtE],
            ast.GtE: [ast.Gt, ast.Lt, ast.LtE],
            ast.Is: [ast.IsNot],
            ast.IsNot: [ast.Is],
            ast.In: [ast.NotIn],
            ast.NotIn: [ast.In],
        }

    def can_mutate(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and type(node.ops[0]) in self.mutations
        )

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            for new_op_class in self.mutations.get(type(node.ops[0]), []):
                mutated = copy.deepcopy(node)
                mutated.ops = [new_op_class()]
                yield mutated


class BooleanOperatorMutator(MutationOperator):
    """Mutates boolean operators (and, or)."""

    def __init__(self) -> None:
        super().__init__("boolean")
        self.mutations = {
            ast.And: [ast.Or],
            ast.Or: [ast.And],
        }

    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.BoolOp) and type(node.op) in self.mutations

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.BoolOp):
            for new_op_class in self.mutations.get(type(node.op), []):
                mutated = copy.deepcopy(node)
                mutated.op = new_op_class()
                yield mutated


class UnaryOperatorMutator(MutationOperator):
    """Mutates unary operators (not, +, -)."""

    def __init__(self) -> None:
        super().__init__("unary")

    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.UnaryOp) and isinstance(
            node.op, (ast.Not, ast.UAdd, ast.USub)
        )

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.Not):
                # Remove 'not' operator
                yield node.operand
            elif isinstance(node.op, ast.UAdd):
                # Change +x to -x
                mutated = copy.deepcopy(node)
                mutated.op = ast.USub()
                yield mutated
            elif isinstance(node.op, ast.USub):
                # Change -x to +x
                mutated = copy.deepcopy(node)
                mutated.op = ast.UAdd()
                yield mutated


class ConstantMutator(MutationOperator):
    """Mutates constants (numbers, strings, booleans)."""

    def __init__(self) -> None:
        super().__init__("constant")

    def can_mutate(self, node: ast.AST) -> bool:
        return isinstance(node, ast.Constant)

    def mutate(self, node: ast.AST) -> Iterator[ast.AST]:
        if isinstance(node, ast.Constant):
            value = node.value

            if isinstance(value, bool):
                # Flip boolean
                mutated = copy.deepcopy(node)
                mutated.value = not value
                yield mutated
            elif isinstance(value, (int, float)) and value != 0:
                # Change number to 0
                mutated = copy.deepcopy(node)
                mutated.value = 0
                yield mutated
                # Change number to 1
                mutated = copy.deepcopy(node)
                mutated.value = 1
                yield mutated
            elif isinstance(value, str) and value:
                # Change string to empty
                mutated = copy.deepcopy(node)
                mutated.value = ""
                yield mutated


class MutationGenerator:
    """Generates mutations for Python code using AST transformation."""

    def __init__(self, operators: list[MutationOperator] | None = None) -> None:
        self.operators = operators or [
            ArithmeticOperatorMutator(),
            ComparisonOperatorMutator(),
            BooleanOperatorMutator(),
            UnaryOperatorMutator(),
            ConstantMutator(),
        ]

    def generate_mutations(
        self, source_code: str, file_path: str
    ) -> list[tuple[str, str, int, str, str]]:
        """Generate all possible mutations for the given source code.

        Returns:
            List of tuples: (mutation_id, mutated_code, line_number, original_snippet, mutated_snippet)
        """
        try:
            tree = ast.parse(source_code, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"Cannot parse {file_path}: {e}")
            return []

        mutations = []
        mutation_id = 0

        for node in ast.walk(tree):
            for operator in self.operators:
                if operator.can_mutate(node):
                    for mutated_node in operator.mutate(node):
                        mutation_id += 1

                        # Create mutated tree
                        mutated_tree = copy.deepcopy(tree)
                        self._replace_node(mutated_tree, node, mutated_node)

                        try:
                            mutated_code = ast.unparse(mutated_tree)
                            line_number = getattr(node, "lineno", 0)

                            # Extract snippets for reporting
                            original_snippet = ast.unparse(node)
                            mutated_snippet = ast.unparse(mutated_node)

                            mutations.append(
                                (
                                    f"{file_path}:{line_number}:{mutation_id}",
                                    mutated_code,
                                    line_number,
                                    original_snippet,
                                    mutated_snippet,
                                )
                            )

                        except Exception as e:
                            logger.debug(
                                f"Failed to generate mutation {mutation_id}: {e}"
                            )
                            continue

        return mutations

    def _replace_node(
        self, tree: ast.AST, target: ast.AST, replacement: ast.AST
    ) -> None:
        """Replace target node with replacement in the tree."""

        class NodeReplacer(ast.NodeTransformer):
            def visit(self, node):
                if node is target:
                    return replacement
                return self.generic_visit(node)

        replacer = NodeReplacer()
        replacer.visit(tree)


class MutationTester:
    """Main mutation testing orchestrator."""

    def __init__(self, timeout_seconds: int = 30) -> None:
        self.timeout_seconds = timeout_seconds
        self.generator = MutationGenerator()

    def run_mutations(
        self,
        target_path: str,
        test_path: str,
        max_mutations: int | None = None,
        module_filter: str | None = None,
    ) -> MutationReport:
        """Run mutation testing on the specified target and test paths."""
        start_time = time.time()

        target_dir = Path(target_path)
        test_dir = Path(test_path)

        if not target_dir.exists():
            raise ValueError(f"Target path does not exist: {target_path}")
        if not test_dir.exists():
            raise ValueError(f"Test path does not exist: {test_path}")

        logger.info(f"Starting mutation testing: {target_path} -> {test_path}")

        # Find Python files to mutate
        python_files = list(target_dir.rglob("*.py"))
        if module_filter:
            python_files = [f for f in python_files if module_filter in str(f)]

        logger.info(f"Found {len(python_files)} Python files to mutate")

        all_mutations = []
        mutation_results = []

        # Generate mutations for all files
        for py_file in python_files:
            if py_file.name.startswith("__"):
                continue  # Skip __init__.py, __pycache__, etc.

            try:
                with open(py_file, encoding="utf-8") as f:
                    source_code = f.read()

                file_mutations = self.generator.generate_mutations(
                    source_code, str(py_file)
                )
                all_mutations.extend(
                    [
                        (
                            py_file,
                            mutation_id,
                            mutated_code,
                            line_number,
                            original,
                            mutated,
                        )
                        for mutation_id, mutated_code, line_number, original, mutated in file_mutations
                    ]
                )

            except Exception as e:
                logger.warning(f"Failed to process {py_file}: {e}")
                continue

        logger.info(f"Generated {len(all_mutations)} total mutations")

        # Limit mutations if requested
        if max_mutations and len(all_mutations) > max_mutations:
            all_mutations = all_mutations[:max_mutations]
            logger.info(f"Limited to {max_mutations} mutations")

        # Run mutations
        for i, (
            file_path,
            mutation_id,
            mutated_code,
            line_number,
            original,
            mutated,
        ) in enumerate(all_mutations):
            logger.debug(f"Running mutation {i+1}/{len(all_mutations)}: {mutation_id}")

            result = self._run_single_mutation(
                file_path,
                mutated_code,
                test_path,
                mutation_id,
                line_number,
                original,
                mutated,
            )
            mutation_results.append(result)

            # Progress update
            if (i + 1) % 10 == 0:
                killed = sum(1 for r in mutation_results if r.killed)
                logger.info(
                    f"Progress: {i+1}/{len(all_mutations)} mutations, {killed} killed"
                )

        # Calculate final statistics
        total_mutations = len(mutation_results)
        killed_mutations = sum(1 for r in mutation_results if r.killed)
        survived_mutations = total_mutations - killed_mutations
        mutation_score = (
            (killed_mutations / total_mutations) if total_mutations > 0 else 0.0
        )

        execution_time = time.time() - start_time

        # Generate summary
        summary: MutationSummary = {
            "mutation_types": {},
            "file_breakdown": {},
            "slowest_mutations": sorted(
                mutation_results, key=lambda r: r.execution_time, reverse=True
            )[:10],
        }

        # Mutation type breakdown
        for result in mutation_results:
            mut_type = result.mutation_type
            if mut_type not in summary["mutation_types"]:
                summary["mutation_types"][mut_type] = {"total": 0, "killed": 0}
            summary["mutation_types"][mut_type]["total"] += 1
            if result.killed:
                summary["mutation_types"][mut_type]["killed"] += 1

        # File breakdown
        for result in mutation_results:
            file_key = str(Path(result.file_path).relative_to(Path.cwd()))
            if file_key not in summary["file_breakdown"]:
                summary["file_breakdown"][file_key] = {"total": 0, "killed": 0}
            summary["file_breakdown"][file_key]["total"] += 1
            if result.killed:
                summary["file_breakdown"][file_key]["killed"] += 1

        return MutationReport(
            target_path=target_path,
            test_path=test_path,
            total_mutations=total_mutations,
            killed_mutations=killed_mutations,
            survived_mutations=survived_mutations,
            mutation_score=mutation_score,
            execution_time=execution_time,
            mutations=mutation_results,
            summary=summary,
        )

    def _run_single_mutation(
        self,
        file_path: Path,
        mutated_code: str,
        test_path: str,
        mutation_id: str,
        line_number: int,
        original_code: str,
        mutated_snippet: str,
    ) -> MutationResult:
        """Run tests against a single mutation."""
        start_time = time.time()

        # Create temporary file with mutation
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(mutated_code)
            temp_file_path = temp_file.name

        try:
            # Backup original file
            original_content = file_path.read_text()

            # Apply mutation
            file_path.write_text(mutated_code)

            # Run tests
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "--tb=no",  # No traceback for speed
                "-q",  # Quiet mode
                "--no-cov",  # No coverage for speed
                "-x",  # Stop on first failure
            ]

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout_seconds,
                    cwd=Path.cwd(),
                )

                # Mutation is "killed" if tests failed (return code != 0)
                killed = result.returncode != 0
                test_output = result.stdout + result.stderr
                error = None

            except subprocess.TimeoutExpired:
                killed = True  # Timeout counts as killed (infinite loop detected)
                test_output = "TIMEOUT"
                error = "Test execution timeout"

            except Exception as e:
                killed = True  # Any error counts as killed
                test_output = str(e)
                error = str(e)

            finally:
                # Restore original file
                file_path.write_text(original_content)

        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

        execution_time = time.time() - start_time

        return MutationResult(
            mutation_id=mutation_id,
            file_path=str(file_path),
            line_number=line_number,
            original_code=original_code,
            mutated_code=mutated_snippet,
            mutation_type=(
                mutation_id.split(":")[-1] if ":" in mutation_id else "unknown"
            ),
            killed=killed,
            test_output=test_output[:500],  # Limit output size
            execution_time=execution_time,
            error=error,
        )

    def generate_html_report(self, report: MutationReport, output_path: Path) -> None:
        """Generate an HTML report from mutation results."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Mutation Testing Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .mutation {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 3px; }}
        .killed {{ background: #d4edda; border-color: #c3e6cb; }}
        .survived {{ background: #f8d7da; border-color: #f5c6cb; }}
        .code {{ font-family: monospace; background: #f8f9fa; padding: 5px; border-radius: 3px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <h1>Mutation Testing Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Target:</strong> {report.target_path}</p>
        <p><strong>Tests:</strong> {report.test_path}</p>
        <p><strong>Total Mutations:</strong> {report.total_mutations}</p>
        <p><strong>Killed Mutations:</strong> {report.killed_mutations}</p>
        <p><strong>Survived Mutations:</strong> {report.survived_mutations}</p>
        <p><strong>Mutation Score:</strong> {report.mutation_score:.2%}</p>
        <p><strong>Execution Time:</strong> {report.execution_time:.2f} seconds</p>
    </div>

    <h2>Mutation Type Breakdown</h2>
    <table>
        <tr><th>Type</th><th>Total</th><th>Killed</th><th>Score</th></tr>
"""

        for mut_type, stats in report.summary["mutation_types"].items():
            score = (stats["killed"] / stats["total"]) if stats["total"] > 0 else 0
            html_content += f"""
        <tr>
            <td>{mut_type}</td>
            <td>{stats['total']}</td>
            <td>{stats['killed']}</td>
            <td>{score:.2%}</td>
        </tr>"""

        html_content += """
    </table>

    <h2>File Breakdown</h2>
    <table>
        <tr><th>File</th><th>Total</th><th>Killed</th><th>Score</th></tr>
"""

        for file_path, stats in report.summary["file_breakdown"].items():
            score = (stats["killed"] / stats["total"]) if stats["total"] > 0 else 0
            html_content += f"""
        <tr>
            <td>{file_path}</td>
            <td>{stats['total']}</td>
            <td>{stats['killed']}</td>
            <td>{score:.2%}</td>
        </tr>"""

        html_content += """
    </table>

    <h2>Survived Mutations (Need Attention)</h2>
"""

        survived_mutations = [m for m in report.mutations if not m.killed]
        for mutation in survived_mutations[:20]:  # Show first 20
            html_content += f"""
    <div class="mutation survived">
        <h3>Line {mutation.line_number} in {Path(mutation.file_path).name}</h3>
        <p><strong>Original:</strong> <span class="code">{mutation.original_code}</span></p>
        <p><strong>Mutated:</strong> <span class="code">{mutation.mutated_code}</span></p>
        <p><strong>Execution Time:</strong> {mutation.execution_time:.2f}s</p>
    </div>"""

        html_content += """
</body>
</html>"""

        with open(output_path, "w") as f:
            f.write(html_content)

    def save_json_report(self, report: MutationReport, output_path: Path) -> None:
        """Save mutation report as JSON."""
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "target_path": report.target_path,
                "test_path": report.test_path,
                "total_mutations": report.total_mutations,
                "killed_mutations": report.killed_mutations,
                "survived_mutations": report.survived_mutations,
                "mutation_score": report.mutation_score,
                "execution_time": report.execution_time,
            },
            "summary": report.summary,
            "mutations": [
                {
                    "mutation_id": m.mutation_id,
                    "file_path": m.file_path,
                    "line_number": m.line_number,
                    "original_code": m.original_code,
                    "mutated_code": m.mutated_code,
                    "mutation_type": m.mutation_type,
                    "killed": m.killed,
                    "execution_time": m.execution_time,
                    "error": m.error,
                }
                for m in report.mutations
            ],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2, sort_keys=True)

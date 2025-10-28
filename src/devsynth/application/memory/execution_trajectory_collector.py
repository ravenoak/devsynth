"""
Execution Trajectory Collector for Code Learning

This module provides execution trajectory collection capabilities for learning
from code execution patterns, addressing the "shallow understanding" problem
identified in the research literature.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from ...domain.models.memory import (
    CognitiveType,
    MemeticMetadata,
    MemeticSource,
    MemeticUnit,
)
from ...logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)


@dataclass
class ExecutionStep:
    """Represents a single step in code execution."""

    step_number: int
    line_number: int
    code_line: str
    variable_states: dict[str, Any] = field(default_factory=dict)
    function_calls: list[str] = field(default_factory=list)
    output: str | None = None
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MemoryState:
    """Represents the memory state at a point in execution."""

    variables: dict[str, Any]
    globals: dict[str, Any]
    locals: dict[str, Any]
    heap_objects: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionTrace:
    """Complete execution trace for a code snippet."""

    code: str
    trace_id: UUID = field(default_factory=uuid4)
    execution_steps: list[ExecutionStep] = field(default_factory=list)
    memory_states: list[MemoryState] = field(default_factory=list)
    variable_changes: dict[str, list[Any]] = field(default_factory=dict)
    function_calls: list[str] = field(default_factory=list)
    execution_outcome: Any | None = None
    execution_error: str | None = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trace_id": str(self.trace_id),
            "code": self.code,
            "execution_steps": [
                {
                    "step_number": step.step_number,
                    "line_number": step.line_number,
                    "code_line": step.code_line,
                    "variable_states": step.variable_states,
                    "function_calls": step.function_calls,
                    "output": step.output,
                    "error": step.error,
                    "timestamp": step.timestamp.isoformat(),
                }
                for step in self.execution_steps
            ],
            "memory_states": [
                {
                    "variables": state.variables,
                    "globals": state.globals,
                    "locals": state.locals,
                    "heap_objects": state.heap_objects,
                }
                for state in self.memory_states
            ],
            "variable_changes": self.variable_changes,
            "function_calls": self.function_calls,
            "execution_outcome": self.execution_outcome,
            "execution_error": self.execution_error,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
        }


class ExecutionTrajectoryCollector:
    """Collect execution trajectories for learning from code behavior."""

    def __init__(self, sandbox_enabled: bool = True, max_execution_time: float = 30.0):
        """Initialize the execution trajectory collector."""
        self.sandbox_enabled = sandbox_enabled
        self.max_execution_time = max_execution_time
        self.execution_history: list[ExecutionTrace] = []

        logger.info(
            f"Execution trajectory collector initialized (sandbox: {sandbox_enabled}, timeout: {max_execution_time}s)"
        )

    def collect_python_trajectories(
        self, code_snippets: list[str]
    ) -> list[ExecutionTrace]:
        """Collect execution traces from Python code snippets."""
        traces = []

        for code in code_snippets:
            try:
                trace = self._execute_in_sandbox(code)
                if trace:
                    traces.append(trace)
                    self.execution_history.append(trace)
            except Exception as e:
                logger.error(f"Failed to collect trajectory for code: {e}")
                # Create error trace
                error_trace = ExecutionTrace(
                    code=code,
                    execution_error=str(e),
                    execution_steps=[
                        ExecutionStep(
                            step_number=1,
                            line_number=0,
                            code_line="ERROR: " + str(e),
                            error=str(e),
                        )
                    ],
                )
                traces.append(error_trace)
                self.execution_history.append(error_trace)

        logger.info(f"Collected {len(traces)} execution trajectories")
        return traces

    def _execute_in_sandbox(self, code: str) -> ExecutionTrace | None:
        """Execute code in isolated environment with comprehensive tracing."""
        # Create a temporary Python file for execution
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            # Execute with timeout and capture output
            start_time = datetime.now()

            # Use subprocess to execute with timeout and capture detailed output
            result = subprocess.run(
                [sys.executable, temp_file_path],
                capture_output=True,
                text=True,
                timeout=self.max_execution_time,
            )

            execution_time = (datetime.now() - start_time).total_seconds()

            # Parse the code for structural analysis
            try:
                tree = ast.parse(code)
                execution_steps = self._analyze_code_structure(tree)
            except SyntaxError as e:
                execution_steps = [
                    ExecutionStep(
                        step_number=1,
                        line_number=e.lineno or 0,
                        code_line=str(e.text or ""),
                        error=f"SyntaxError: {e.msg}",
                    )
                ]

            # Create execution trace
            trace = ExecutionTrace(
                code=code,
                execution_steps=execution_steps,
                execution_outcome=result.stdout,
                execution_error=result.stderr if result.returncode != 0 else None,
                execution_time=execution_time,
            )

            return trace

        except subprocess.TimeoutExpired:
            logger.warning(f"Execution timeout for code: {code[:50]}...")
            return ExecutionTrace(
                code=code,
                execution_error=f"Timeout after {self.max_execution_time} seconds",
                execution_time=self.max_execution_time,
            )

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return ExecutionTrace(code=code, execution_error=str(e))

        finally:
            # Clean up temporary file
            try:
                import os

                os.unlink(temp_file_path)
            except Exception:
                pass  # Ignore cleanup errors

    def _analyze_code_structure(self, tree: ast.AST) -> list[ExecutionStep]:
        """Analyze AST structure to create execution steps."""
        steps = []

        class ExecutionAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.current_line = 0
                self.steps = []

            def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
                """Visit function definition."""
                self.steps.append(
                    ExecutionStep(
                        step_number=len(self.steps) + 1,
                        line_number=node.lineno,
                        code_line=f"def {node.name}({', '.join(arg.arg for arg in node.args.args)}):",
                    )
                )
                self.generic_visit(node)

            def visit_Assign(self, node: ast.Assign) -> None:
                """Visit variable assignment."""
                if node.targets and hasattr(node.targets[0], "id"):
                    var_name = node.targets[0].id
                    self.steps.append(
                        ExecutionStep(
                            step_number=len(self.steps) + 1,
                            line_number=node.lineno,
                            code_line=f"{var_name} = ...",
                            variable_states={var_name: "assigned"},
                        )
                    )
                self.generic_visit(node)

            def visit_Call(self, node: ast.Call) -> None:
                """Visit function call."""
                if hasattr(node.func, "id"):
                    func_name = node.func.id
                elif hasattr(node.func, "attr"):
                    func_name = node.func.attr
                else:
                    func_name = "unknown"

                self.steps.append(
                    ExecutionStep(
                        step_number=len(self.steps) + 1,
                        line_number=node.lineno,
                        code_line=f"{func_name}()",
                        function_calls=[func_name],
                    )
                )
                self.generic_visit(node)

        analyzer = ExecutionAnalyzer()
        analyzer.visit(tree)

        return (
            analyzer.steps
            if analyzer.steps
            else [
                ExecutionStep(
                    step_number=1, line_number=1, code_line="Code analysis complete"
                )
            ]
        )

    def extract_execution_patterns(
        self, traces: list[ExecutionTrace]
    ) -> dict[str, Any]:
        """Extract patterns from execution trajectories."""
        patterns = {
            "function_call_patterns": {},
            "variable_usage_patterns": {},
            "error_patterns": {},
            "performance_patterns": {},
        }

        for trace in traces:
            # Analyze function call patterns
            for step in trace.execution_steps:
                for func_call in step.function_calls:
                    if func_call not in patterns["function_call_patterns"]:
                        patterns["function_call_patterns"][func_call] = {
                            "count": 0,
                            "contexts": [],
                            "outcomes": [],
                        }

                    patterns["function_call_patterns"][func_call]["count"] += 1
                    patterns["function_call_patterns"][func_call]["contexts"].append(
                        {"line": step.line_number, "code_context": step.code_line}
                    )

                    if trace.execution_outcome:
                        patterns["function_call_patterns"][func_call][
                            "outcomes"
                        ].append("success" if not trace.execution_error else "error")

            # Analyze variable usage patterns
            for var_name, changes in trace.variable_changes.items():
                if var_name not in patterns["variable_usage_patterns"]:
                    patterns["variable_usage_patterns"][var_name] = {
                        "change_count": 0,
                        "change_types": [],
                        "final_value": None,
                    }

                patterns["variable_usage_patterns"][var_name]["change_count"] += len(
                    changes
                )

            # Analyze error patterns
            if trace.execution_error:
                error_type = self._classify_error_type(trace.execution_error)
                if error_type not in patterns["error_patterns"]:
                    patterns["error_patterns"][error_type] = 0
                patterns["error_patterns"][error_type] += 1

            # Analyze performance patterns
            if trace.execution_time > 0:
                perf_category = self._categorize_performance(trace.execution_time)
                if perf_category not in patterns["performance_patterns"]:
                    patterns["performance_patterns"][perf_category] = []
                patterns["performance_patterns"][perf_category].append(
                    {
                        "execution_time": trace.execution_time,
                        "line_count": len(trace.execution_steps),
                        "error": trace.execution_error is not None,
                    }
                )

        logger.info(f"Extracted patterns from {len(traces)} traces")
        return patterns

    def _classify_error_type(self, error_message: str) -> str:
        """Classify error message into categories."""
        error_lower = error_message.lower()

        if any(
            keyword in error_lower
            for keyword in ["nameerror", "undefined", "not defined"]
        ):
            return "NameError"
        elif any(keyword in error_lower for keyword in ["typeerror", "type", "cannot"]):
            return "TypeError"
        elif any(
            keyword in error_lower for keyword in ["valueerror", "invalid", "value"]
        ):
            return "ValueError"
        elif any(
            keyword in error_lower for keyword in ["indexerror", "index", "range"]
        ):
            return "IndexError"
        elif any(
            keyword in error_lower for keyword in ["keyerror", "key", "not found"]
        ):
            return "KeyError"
        elif any(keyword in error_lower for keyword in ["attributeerror", "attribute"]):
            return "AttributeError"
        elif any(
            keyword in error_lower for keyword in ["importerror", "import", "module"]
        ):
            return "ImportError"
        elif any(keyword in error_lower for keyword in ["syntaxerror", "syntax"]):
            return "SyntaxError"
        else:
            return "OtherError"

    def _categorize_performance(self, execution_time: float) -> str:
        """Categorize execution time into performance categories."""
        if execution_time < 0.1:
            return "very_fast"
        elif execution_time < 1.0:
            return "fast"
        elif execution_time < 5.0:
            return "moderate"
        elif execution_time < 15.0:
            return "slow"
        else:
            return "very_slow"

    def create_memetic_units_from_trajectories(
        self, traces: list[ExecutionTrace]
    ) -> list[MemeticUnit]:
        """Create Memetic Units from execution trajectories."""
        units = []

        for trace in traces:
            # Create episodic memory unit for the execution experience
            episodic_unit = MemeticUnit(
                metadata=MemeticMetadata(
                    source=MemeticSource.CODE_EXECUTION,
                    cognitive_type=CognitiveType.EPISODIC,
                    content_hash=str(trace.trace_id),
                    topic="execution_trajectory",
                    confidence_score=0.9,  # High confidence for execution data
                    status=self._determine_trace_status(trace),
                ),
                payload=trace.to_dict(),
            )

            # Extract patterns and create semantic units
            patterns = self.extract_execution_patterns([trace])

            for pattern_type, pattern_data in patterns.items():
                if pattern_data:  # Only create units for non-empty patterns
                    semantic_unit = MemeticUnit(
                        metadata=MemeticMetadata(
                            source=MemeticSource.CODE_EXECUTION,
                            cognitive_type=CognitiveType.SEMANTIC,
                            content_hash=self._compute_pattern_hash(pattern_data),
                            topic=f"execution_pattern_{pattern_type}",
                            keywords=self._extract_pattern_keywords(pattern_data),
                            confidence_score=0.8,
                            summary=f"Pattern extracted from execution trace: {pattern_type}",
                        ),
                        payload={
                            "pattern_type": pattern_type,
                            "pattern_data": pattern_data,
                            "source_trace": str(trace.trace_id),
                        },
                    )

                    units.append(semantic_unit)

            units.append(episodic_unit)

        logger.info(
            f"Created {len(units)} Memetic Units from {len(traces)} execution traces"
        )
        return units

    def _determine_trace_status(self, trace: ExecutionTrace) -> Any:
        """Determine status of execution trace."""
        from ...domain.models.memory import MemeticStatus

        if trace.execution_error:
            return MemeticStatus.PROCESSED  # Error traces are still valuable
        elif trace.execution_time > self.max_execution_time * 0.8:
            return MemeticStatus.CONSOLIDATED  # Long-running traces are significant
        else:
            return MemeticStatus.PROCESSED

    def _compute_pattern_hash(self, pattern_data: Any) -> str:
        """Compute hash for pattern data."""
        import hashlib
        import json

        # Normalize pattern data for consistent hashing
        normalized = json.dumps(pattern_data, sort_keys=True, default=str)
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _extract_pattern_keywords(self, pattern_data: Any) -> list[str]:
        """Extract keywords from pattern data."""
        keywords = []

        if isinstance(pattern_data, dict):
            # Extract keys as keywords
            keywords.extend(pattern_data.keys())

            # Extract values if they're strings
            for value in pattern_data.values():
                if isinstance(value, str):
                    keywords.extend(value.split())
                elif isinstance(value, list) and value and isinstance(value[0], str):
                    keywords.extend(value[:3])  # First few items

        return keywords[:10]  # Limit to 10 keywords

    def batch_collect_trajectories(
        self, code_batch: list[str], batch_size: int = 5
    ) -> list[ExecutionTrace]:
        """Collect trajectories in batches for efficiency."""
        all_traces = []

        # Process in batches to avoid overwhelming the system
        for i in range(0, len(code_batch), batch_size):
            batch = code_batch[i : i + batch_size]
            batch_traces = self.collect_python_trajectories(batch)
            all_traces.extend(batch_traces)

            # Small delay between batches to avoid overwhelming
            if i + batch_size < len(code_batch):
                import time

                time.sleep(0.1)

        return all_traces

    def get_execution_insights(self, traces: list[ExecutionTrace]) -> dict[str, Any]:
        """Extract insights from execution trajectories."""
        if not traces:
            return {"error": "No execution traces provided"}

        insights = {
            "total_traces": len(traces),
            "successful_executions": sum(1 for t in traces if not t.execution_error),
            "failed_executions": sum(1 for t in traces if t.execution_error),
            "average_execution_time": sum(t.execution_time for t in traces)
            / len(traces),
            "performance_distribution": {},
            "error_distribution": {},
            "common_patterns": self.extract_execution_patterns(traces),
        }

        # Performance distribution
        perf_categories = ["very_fast", "fast", "moderate", "slow", "very_slow"]
        for category in perf_categories:
            count = sum(
                1
                for t in traces
                if self._categorize_performance(t.execution_time) == category
            )
            insights["performance_distribution"][category] = count

        # Error distribution
        for trace in traces:
            if trace.execution_error:
                error_type = self._classify_error_type(trace.execution_error)
                insights["error_distribution"][error_type] = (
                    insights["error_distribution"].get(error_type, 0) + 1
                )

        return insights

    def validate_trajectory_quality(self, trace: ExecutionTrace) -> dict[str, Any]:
        """Validate quality of execution trajectory."""
        quality_metrics = {
            "trace_id": str(trace.trace_id),
            "completeness_score": 0.0,
            "clarity_score": 0.0,
            "usefulness_score": 0.0,
            "overall_quality": 0.0,
            "issues": [],
        }

        # Completeness: should have execution steps and outcome
        if trace.execution_steps:
            quality_metrics["completeness_score"] = 0.8
        else:
            quality_metrics["issues"].append("No execution steps recorded")
            quality_metrics["completeness_score"] = 0.0

        # Clarity: should have clear error messages or successful outcomes
        if trace.execution_error:
            if len(trace.execution_error) > 10:  # Meaningful error message
                quality_metrics["clarity_score"] = 0.9
            else:
                quality_metrics["clarity_score"] = 0.3
                quality_metrics["issues"].append("Unclear error message")
        elif trace.execution_outcome:
            quality_metrics["clarity_score"] = 0.8
        else:
            quality_metrics["clarity_score"] = 0.4
            quality_metrics["issues"].append("No clear outcome")

        # Usefulness: based on execution time and information content
        if trace.execution_time > 0 and trace.execution_time < self.max_execution_time:
            quality_metrics["usefulness_score"] = 0.8
        elif trace.execution_time >= self.max_execution_time:
            quality_metrics["usefulness_score"] = 0.5
            quality_metrics["issues"].append("Execution timed out")
        else:
            quality_metrics["usefulness_score"] = 0.6

        # Overall quality
        quality_metrics["overall_quality"] = (
            quality_metrics["completeness_score"] * 0.4
            + quality_metrics["clarity_score"] * 0.3
            + quality_metrics["usefulness_score"] * 0.3
        )

        return quality_metrics

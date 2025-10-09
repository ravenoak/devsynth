"""Typed AST-based code transformation utilities."""

from __future__ import annotations

import ast
import warnings
from contextlib import contextmanager
from dataclasses import dataclass, field
from types import ModuleType
from typing import Iterable, List, Optional, Sequence, Set, Union, cast

from devsynth.logging_setup import DevSynthLogger

from .transformers import (
    ClassExtractionRequest,
    DocstringSpec,
    FunctionToClassExtractor,
    FunctionToMethodConverter,
    MethodConversionPlan,
    apply_docstring_spec,
)

logger = DevSynthLogger(__name__)

try:
    import astor as _astor

    HAS_ASTOR = True
    astor: Optional[ModuleType] = _astor
except ImportError:  # pragma: no cover - exercised when astor is absent
    logger.warning(
        "astor library not found. Using fallback implementation for to_source."
    )
    HAS_ASTOR = False
    astor = None


@contextmanager
def suppress_deprecation_warnings() -> Iterable[None]:
    """Context manager to suppress deprecation warnings."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        yield


def to_source_with_suppressed_warnings(node: ast.AST) -> str:
    """Convert an AST node to source code while silencing deprecation warnings."""
    with suppress_deprecation_warnings():
        if HAS_ASTOR and astor is not None:
            try:
                try:
                    return astor.to_source(node)
                except AttributeError:
                    return astor.code_gen.to_source(node)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to use astor for code generation: %s", exc)
        try:
            return ast.unparse(node)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to unparse AST node: %s", exc)
            return (
                f"# Failed to generate source code: {exc}\n"
                "# Please install astor library for better results"
            )


@dataclass(frozen=True)
class FunctionExtractionRequest:
    """Information required to extract a function from a block of code."""

    start_line: int
    end_line: int
    function_name: str
    parameters: Sequence[str] = field(default_factory=tuple)


class IdentifierRenamer(ast.NodeTransformer):
    """Rename occurrences of an identifier in an AST tree."""

    def __init__(self, old_name: str, new_name: str) -> None:
        self.old_name = old_name
        self.new_name = new_name
        self.changed: bool = False

    def visit_Name(
        self, node: ast.Name
    ) -> ast.AST:  # noqa: N802 - required by ast.NodeTransformer
        if node.id == self.old_name:
            self.changed = True
            return ast.copy_location(ast.Name(id=self.new_name, ctx=node.ctx), node)
        return self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
        if node.name == self.old_name:
            self.changed = True
            node.name = self.new_name
        for arg in node.args.args:
            if arg.arg == self.old_name:
                self.changed = True
                arg.arg = self.new_name
        if node.args.vararg and node.args.vararg.arg == self.old_name:
            self.changed = True
            node.args.vararg.arg = self.new_name
        if node.args.kwarg and node.args.kwarg.arg == self.old_name:
            self.changed = True
            node.args.kwarg.arg = self.new_name
        for kwonly in node.args.kwonlyargs:
            if kwonly.arg == self.old_name:
                self.changed = True
                kwonly.arg = self.new_name
        return self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:  # noqa: N802
        if node.name == self.old_name:
            self.changed = True
            node.name = self.new_name
        return self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:  # noqa: N802
        if node.attr == self.old_name:
            self.changed = True
            node.attr = self.new_name
        return self.generic_visit(node)


class UsedNameCollector(ast.NodeVisitor):
    """Collect names that are read from within an AST tree."""

    def __init__(self) -> None:
        self.used_names: Set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:  # noqa: N802
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)


class UnusedImportRemover(ast.NodeTransformer):
    """Remove import statements whose bindings are never referenced."""

    def __init__(self, used_names: Set[str]) -> None:
        self.used_names = used_names

    def visit_Import(self, node: ast.Import) -> Union[ast.Import, None]:  # noqa: N802
        filtered = [alias for alias in node.names if self._alias_used(alias)]
        if not filtered:
            return None
        node.names = filtered
        return node

    def visit_ImportFrom(
        self, node: ast.ImportFrom
    ) -> Union[ast.ImportFrom, None]:  # noqa: N802
        filtered = [alias for alias in node.names if self._alias_used(alias)]
        if not filtered:
            return None
        node.names = filtered
        return node

    def _alias_used(self, alias: ast.alias) -> bool:
        name = alias.asname or alias.name.split(".")[0]
        return name in self.used_names


class UnusedVariableRemover(ast.NodeTransformer):
    """Remove assignments to variables that are never read."""

    def __init__(self, used_names: Set[str]) -> None:
        self.used_names = used_names

    def visit_Assign(self, node: ast.Assign) -> Union[ast.Assign, None]:  # noqa: N802
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            target = node.targets[0].id
            if target not in self.used_names:
                return None
        return self.generic_visit(node)


class RedundantAssignmentRemover(ast.NodeTransformer):
    """Remove consecutive assignments that overwrite the same variable."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
        node = cast(ast.FunctionDef, self.generic_visit(node))
        node.body = self._prune_assignments(node.body)
        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AST:  # noqa: N802
        node = cast(ast.AsyncFunctionDef, self.generic_visit(node))
        node.body = self._prune_assignments(node.body)
        return node

    def _prune_assignments(self, body: List[ast.stmt]) -> List[ast.stmt]:
        result: List[ast.stmt] = []
        for statement in body:
            if isinstance(statement, ast.Assign) and _single_name_target(statement):
                if (
                    result
                    and isinstance(result[-1], ast.Assign)
                    and _single_name_target(result[-1])
                    and cast(ast.Name, result[-1].targets[0]).id
                    == cast(ast.Name, statement.targets[0]).id
                ):
                    result[-1] = statement
                    continue
            self._process_nested(statement)
            result.append(statement)
        return result

    def _process_nested(self, statement: ast.stmt) -> None:
        if isinstance(statement, (ast.If, ast.For, ast.While, ast.With, ast.AsyncWith)):
            statement.body = self._prune_assignments(statement.body)
            statement.orelse = self._prune_assignments(statement.orelse)
        elif isinstance(statement, (ast.Try,)):
            statement.body = self._prune_assignments(statement.body)
            statement.orelse = self._prune_assignments(statement.orelse)
            statement.finalbody = self._prune_assignments(statement.finalbody)
            for handler in statement.handlers:
                handler.body = self._prune_assignments(handler.body)


class StringLiteralOptimizer(ast.NodeTransformer):
    """Convert simple string concatenations into f-strings."""

    def visit_Assign(self, node: ast.Assign) -> ast.AST:  # noqa: N802
        node = cast(ast.Assign, self.generic_visit(node))
        if isinstance(node.value, ast.BinOp):
            parts = list(_flatten_string_concatenation(node.value))
            joined_values = _to_joined_str(parts)
            if joined_values:
                node.value = ast.JoinedStr(values=joined_values)
        return node


class TypeHintAdder(ast.NodeTransformer):
    """Add `-> None` return annotations to functions lacking them."""

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:  # noqa: N802
        node = cast(ast.FunctionDef, self.generic_visit(node))
        if node.returns is None:
            node.returns = ast.Name(id="None", ctx=ast.Load())
        return node

    def visit_AsyncFunctionDef(
        self, node: ast.AsyncFunctionDef
    ) -> ast.AST:  # noqa: N802
        node = cast(ast.AsyncFunctionDef, self.generic_visit(node))
        if node.returns is None:
            node.returns = ast.Name(id="None", ctx=ast.Load())
        return node


def _single_name_target(node: ast.Assign) -> bool:
    return len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)


def _flatten_string_concatenation(node: ast.AST) -> Iterable[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        yield from _flatten_string_concatenation(node.left)
        yield from _flatten_string_concatenation(node.right)
    else:
        yield node


def _to_joined_str(parts: Iterable[ast.AST]) -> List[ast.AST]:
    joined: List[ast.AST] = []
    for part in parts:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            joined.append(ast.Constant(value=part.value))
        elif isinstance(part, ast.Name):
            joined.append(
                ast.FormattedValue(
                    value=ast.Name(id=part.id, ctx=ast.Load()), conversion=-1
                )
            )
        else:
            return []
    return joined


class AstTransformer:
    """High-level helper for manipulating Python code via the AST."""

    def rename_identifier(self, code: str, old_name: str, new_name: str) -> str:
        tree = ast.parse(code)
        transformer = IdentifierRenamer(old_name, new_name)
        new_tree = transformer.visit(tree)
        if not transformer.changed:
            return code
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def extract_function(self, code: str, request: FunctionExtractionRequest) -> str:
        tree = ast.parse(code)
        start_line = request.start_line - 1
        end_line = request.end_line - 1
        lines = code.splitlines()
        if start_line < 0 or end_line >= len(lines) or start_line > end_line:
            raise ValueError(
                f"Invalid line range: {request.start_line} to {request.end_line}"
            )

        block_lines = lines[start_line : end_line + 1]
        indentation = (
            len(block_lines[0]) - len(block_lines[0].lstrip()) if block_lines else 0
        )
        dedented_block = [
            line[indentation:] if line.strip() else "" for line in block_lines
        ]

        params = ", ".join(request.parameters)
        function_header = f"def {request.function_name}({params}):"
        function_body = "\n".join(
            "    " + line if line else "" for line in dedented_block
        )
        function_code = (
            f"{function_header}\n{function_body}"
            if function_body
            else f"{function_header}\n    pass"
        )

        call_args = ", ".join(request.parameters)
        call_line = " " * indentation + f"{request.function_name}({call_args})"

        new_lines = lines[:start_line] + [call_line] + lines[end_line + 1 :]
        new_lines.insert(0, "")
        new_lines.insert(0, function_code)
        new_code = "\n".join(new_lines)
        ast.parse(new_code)
        return new_code

    def add_docstring(self, code: str, spec: DocstringSpec) -> str:
        tree = ast.parse(code)
        result = apply_docstring_spec(tree, spec)
        if not result.target_found:
            raise ValueError(f"Target '{spec.target or 'module'}' not found")
        ast.fix_missing_locations(result.tree)
        return to_source_with_suppressed_warnings(result.tree)

    def validate_syntax(self, code: str) -> bool:
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def add_type_hints(self, code: str) -> str:
        tree = ast.parse(code)
        transformer = TypeHintAdder()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def convert_function_to_method(self, code: str, plan: MethodConversionPlan) -> str:
        tree = ast.parse(code)
        transformer = FunctionToMethodConverter(plan)
        new_tree = transformer.visit(tree)
        if not transformer.function_found:
            raise ValueError(f"Function '{plan.function_name}' not found")
        if not transformer.class_found:
            raise ValueError(f"Class '{plan.class_name}' not found")
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def extract_class(self, code: str, request: ClassExtractionRequest) -> str:
        tree = ast.parse(code)
        transformer = FunctionToClassExtractor(request)
        new_tree = transformer.visit(tree)
        if transformer.missing_functions:
            missing = ", ".join(transformer.missing_functions)
            raise ValueError(f"Functions not found: {missing}")
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def remove_unused_imports(self, code: str) -> str:
        tree = ast.parse(code)
        collector = UsedNameCollector()
        collector.visit(tree)
        transformer = UnusedImportRemover(collector.used_names)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def remove_redundant_assignments(self, code: str) -> str:
        tree = ast.parse(code)
        transformer = RedundantAssignmentRemover()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def remove_unused_variables(self, code: str) -> str:
        tree = ast.parse(code)
        collector = UsedNameCollector()
        collector.visit(tree)
        transformer = UnusedVariableRemover(collector.used_names)
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def optimize_string_literals(self, code: str) -> str:
        tree = ast.parse(code)
        transformer = StringLiteralOptimizer()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        return to_source_with_suppressed_warnings(new_tree)

    def apply_common_fixes(self, code: str) -> str:
        code = self.add_type_hints(code)
        code = self.remove_unused_imports(code)
        code = self.remove_unused_variables(code)
        return code

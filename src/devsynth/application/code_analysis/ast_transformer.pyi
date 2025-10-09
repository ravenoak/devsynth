"""Type hints for devsynth.application.code_analysis.ast_transformer."""

from __future__ import annotations

import ast
from typing import Iterable, Iterator, Literal, Sequence

MethodType = Literal["instance", "class", "static"]

class FunctionExtractionRequest:
    start_line: int
    end_line: int
    function_name: str
    parameters: Sequence[str]

    def __init__(
        self,
        start_line: int,
        end_line: int,
        function_name: str,
        parameters: Sequence[str] = ...,
    ) -> None: ...

class DocstringSpec:
    target: str | None
    docstring: str

    def __init__(self, target: str | None, docstring: str) -> None: ...

class MethodConversionPlan:
    function_name: str
    class_name: str
    method_type: MethodType

    def __init__(
        self,
        function_name: str,
        class_name: str,
        method_type: MethodType = ...,
    ) -> None: ...

class ClassExtractionRequest:
    functions: Sequence[str]
    class_name: str
    base_classes: Sequence[str]
    docstring: str | None

    def __init__(
        self,
        functions: Sequence[str],
        class_name: str,
        base_classes: Sequence[str] = ...,
        docstring: str | None = ...,
    ) -> None: ...

def suppress_deprecation_warnings() -> Iterator[None]: ...
def to_source_with_suppressed_warnings(node: ast.AST) -> str: ...

class AstTransformer:
    """High-level helper for manipulating Python code via the AST."""

    def rename_identifier(self, code: str, old_name: str, new_name: str) -> str: ...
    def extract_function(
        self, code: str, request: FunctionExtractionRequest
    ) -> str: ...
    def add_docstring(self, code: str, spec: DocstringSpec) -> str: ...
    def validate_syntax(self, code: str) -> bool: ...
    def add_type_hints(self, code: str) -> str: ...
    def convert_function_to_method(
        self, code: str, plan: MethodConversionPlan
    ) -> str: ...
    def extract_class(self, code: str, request: ClassExtractionRequest) -> str: ...
    def remove_unused_imports(self, code: str) -> str: ...
    def remove_redundant_assignments(self, code: str) -> str: ...
    def remove_unused_variables(self, code: str) -> str: ...
    def optimize_string_literals(self, code: str) -> str: ...
    def apply_common_fixes(self, code: str) -> str: ...

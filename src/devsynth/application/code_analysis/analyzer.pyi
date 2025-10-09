"""Type hints for devsynth.application.code_analysis.analyzer."""

from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional, Protocol, TypedDict

from devsynth.domain.models.code_analysis import CodeAnalysis, FileAnalysis

class ImportInfo(TypedDict, total=False):
    name: str
    path: str
    line: int
    col: int
    from_module: str

class ClassInfo(TypedDict):
    name: str
    line: int
    col: int
    docstring: str
    methods: List[str]
    attributes: List[str]
    bases: List[str]

class FunctionInfo(TypedDict):
    name: str
    line: int
    col: int
    docstring: str
    params: List[str]
    return_type: str

class VariableInfo(TypedDict):
    name: str
    line: int
    col: int
    type: str

class SymbolReference(TypedDict):
    file: str
    line: int
    column: int
    type: str

class AstVisitor(ast.NodeVisitor):
    imports: List[ImportInfo]
    classes: List[ClassInfo]
    functions: List[FunctionInfo]
    variables: List[VariableInfo]
    docstring: str
    current_class: Optional[ClassInfo]
    line_count: int

class _CodeAnalysisProvider(Protocol):
    def analyze_file(self, file_path: str) -> FileAnalysis: ...
    def analyze_directory(
        self, dir_path: str, recursive: bool = ...
    ) -> CodeAnalysis: ...
    def analyze_code(self, code: str, file_name: str = ...) -> FileAnalysis: ...
    def analyze_project_structure(
        self,
        exploration_depth: str = ...,
        include_dependencies: bool = ...,
        extract_relationships: bool = ...,
    ) -> Dict[str, Any]: ...

class CodeAnalyzer(_CodeAnalysisProvider):
    """Implementation of :class:`CodeAnalysisProvider` for Python source."""

    def analyze_file(self, file_path: str) -> FileAnalysis: ...
    def analyze_directory(
        self, dir_path: str, recursive: bool = ...
    ) -> CodeAnalysis: ...
    def analyze_code(self, code: str, file_name: str = ...) -> FileAnalysis: ...
    def analyze_project_structure(
        self,
        exploration_depth: str = ...,
        include_dependencies: bool = ...,
        extract_relationships: bool = ...,
    ) -> Dict[str, Any]: ...
    def _find_python_files(self, dir_path: str, recursive: bool) -> List[str]: ...
    def _get_module_name(self, file_path: str, base_dir: str) -> str: ...
    def _extract_symbols(
        self,
        file_path: str,
        file_analysis: FileAnalysis,
        symbols: Dict[str, List[SymbolReference]],
    ) -> None: ...

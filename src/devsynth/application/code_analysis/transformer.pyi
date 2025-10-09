"""Type hints for devsynth.application.code_analysis.transformer."""

from __future__ import annotations

from typing import Dict, List, Optional, Protocol, TypedDict

from devsynth.application.code_analysis.analyzer import CodeAnalyzer
from devsynth.domain.interfaces.code_analysis import TransformationResult
from devsynth.domain.models.code_analysis import CodeTransformation

class ChangeRecord(TypedDict, total=False):
    description: str
    line: int
    col: int

class _CodeTransformationProvider(Protocol):
    def transform_code(
        self, code: str, transformations: Optional[List[str]] = ...
    ) -> CodeTransformation: ...
    def transform_file(
        self, file_path: str, transformations: Optional[List[str]] = ...
    ) -> CodeTransformation: ...
    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = ...,
        transformations: Optional[List[str]] = ...,
    ) -> Dict[str, TransformationResult]: ...

class CodeTransformer(_CodeTransformationProvider):
    analyzer: CodeAnalyzer
    transformers: Dict[str, type]

    def __init__(self) -> None: ...
    def transform_code(
        self, code: str, transformations: Optional[List[str]] = ...
    ) -> CodeTransformation: ...
    def transform_file(
        self, file_path: str, transformations: Optional[List[str]] = ...
    ) -> CodeTransformation: ...
    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = ...,
        transformations: Optional[List[str]] = ...,
    ) -> Dict[str, TransformationResult]: ...

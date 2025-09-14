"""
Domain interfaces for code analysis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class FileAnalysisResult(ABC):
    """Interface for the result of analyzing a single file."""

    @abstractmethod
    def get_imports(self) -> list[dict[str, Any]]:
        """Get the imports found in the file.

        Returns:
            A list of dictionaries containing import information.
             Each dictionary should have at least
             'name' and 'path' keys.
        """
        raise NotImplementedError

    @abstractmethod
    def get_classes(self) -> list[dict[str, Any]]:
        """Get the classes found in the file.

        Returns:
            A list of dictionaries containing class information.
             Each dictionary should have at least
             'name', 'methods', and 'attributes' keys.
        """
        raise NotImplementedError

    @abstractmethod
    def get_functions(self) -> list[dict[str, Any]]:
        """Get the functions found in the file.

        Returns:
            A list of dictionaries containing function information.
             Each dictionary should have at least
             'name', 'params', and 'return_type' keys.
        """
        raise NotImplementedError

    @abstractmethod
    def get_variables(self) -> list[dict[str, Any]]:
        """Get the variables found in the file.

        Returns:
            A list of dictionaries containing variable information.
            Each dictionary should have at least 'name' and 'type' keys.
        """
        raise NotImplementedError

    @abstractmethod
    def get_docstring(self) -> str:
        """Get the module-level docstring of the file.

        Returns:
            The docstring as a string, or an empty string if no docstring is found.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get metrics about the file.

        Returns:
            A dictionary of metrics, such as lines of code, complexity, etc.
        """
        raise NotImplementedError


class CodeAnalysisResult(ABC):
    """Interface for the result of analyzing a codebase."""

    @abstractmethod
    def get_file_analysis(self, file_path: str) -> FileAnalysisResult | None:
        """Get the analysis result for a specific file.

        Args:
            file_path: The path to the file.

        Returns:
            The FileAnalysisResult for the file, or None if the file was not analyzed.
        """
        raise NotImplementedError

    @abstractmethod
    def get_symbol_references(self, symbol_name: str) -> list[dict[str, Any]]:
        """Get all references to a symbol in the codebase.

        Args:
            symbol_name: The name of the symbol to find references for.

        Returns:
            A list of dictionaries containing reference information.
            Each dictionary should have at least 'file', 'line', and 'column' keys.
        """
        raise NotImplementedError

    @abstractmethod
    def get_dependencies(self, module_name: str) -> list[str]:
        """Get the dependencies of a module.

        Args:
            module_name: The name of the module.

        Returns:
            A list of module names that the specified module depends on.
        """
        raise NotImplementedError

    @abstractmethod
    def get_metrics(self) -> dict[str, Any]:
        """Get metrics about the codebase.

        Returns:
            A dictionary of metrics, such as total lines of code, number of files, etc.
        """
        raise NotImplementedError


class TransformationResult(ABC):
    """Interface for the result of code transformation."""

    @abstractmethod
    def get_original_code(self) -> str:
        """Get the original code before transformation.

        Returns:
            The original code as a string.
        """
        raise NotImplementedError

    @abstractmethod
    def get_transformed_code(self) -> str:
        """Get the transformed code after transformation.

        Returns:
            The transformed code as a string.
        """
        raise NotImplementedError

    @abstractmethod
    def get_changes(self) -> list[dict[str, Any]]:
        """Get the changes made during transformation.

        Returns:
            A list of dictionaries containing change information.
            Each dictionary should have at least a 'description' key.
        """
        raise NotImplementedError


class CodeTransformationProvider(ABC):
    """Interface for code transformation providers."""

    @abstractmethod
    def transform_code(
        self, code: str, transformations: list[str] = None
    ) -> TransformationResult:
        """Transform the given code using the specified transformations.

        Args:
            code: The code to transform.
            transformations: List of transformation names to apply.
            If None, all transformations are applied.

        Returns:
            A TransformationResult containing the transformed code and changes made.
        """
        raise NotImplementedError

    @abstractmethod
    def transform_file(
        self, file_path: str, transformations: list[str] = None
    ) -> TransformationResult:
        """Transform the code in the given file using the specified transformations.

        Args:
            file_path: The path to the file to transform.
            transformations: List of transformation names to apply.
            If None, all transformations are applied.

        Returns:
            A TransformationResult containing the transformed code and changes made.
        """
        raise NotImplementedError

    @abstractmethod
    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = True,
        transformations: list[str] = None,
    ) -> dict[str, TransformationResult]:
        """Transform all Python files in the given directory using the
        specified transformations.

        Args:
            dir_path: The path to the directory to transform.
            recursive: Whether to recursively transform files in subdirectories.
            transformations: List of transformation names to apply.
            If None, all transformations are applied.

        Returns:
            A dictionary mapping file paths to TransformationResult objects.
        """
        raise NotImplementedError


class CodeAnalysisProvider(ABC):
    """Interface for code analysis providers."""

    @abstractmethod
    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        """Analyze a single file.

        Args:
            file_path: The path to the file to analyze.

        Returns:
            A FileAnalysisResult containing the analysis of the file.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_directory(
        self, dir_path: str, recursive: bool = True
    ) -> CodeAnalysisResult:
        """Analyze a directory of files.

        Args:
            dir_path: The path to the directory to analyze.
            recursive: Whether to recursively analyze subdirectories.

        Returns:
            A CodeAnalysisResult containing the analysis of the directory.
        """
        raise NotImplementedError

    @abstractmethod
    def analyze_code(
        self, code: str, file_name: str = "<string>"
    ) -> FileAnalysisResult:
        """Analyze a string of code.

        Args:
            code: The code to analyze.
            file_name: A name for the code, used in error messages.

        Returns:
            A FileAnalysisResult containing the analysis of the code.
        """
        raise NotImplementedError


class SimpleFileAnalysis(FileAnalysisResult):
    """Basic implementation of :class:`FileAnalysisResult`."""

    def __init__(
        self,
        imports: list[dict[str, Any]] | None = None,
        classes: list[dict[str, Any]] | None = None,
        functions: list[dict[str, Any]] | None = None,
        variables: list[dict[str, Any]] | None = None,
        docstring: str = "",
        metrics: dict[str, Any] | None = None,
    ) -> None:
        self._imports = imports or []
        self._classes = classes or []
        self._functions = functions or []
        self._variables = variables or []
        self._docstring = docstring
        self._metrics = metrics or {}

    def get_imports(self) -> list[dict[str, Any]]:
        return self._imports

    def get_classes(self) -> list[dict[str, Any]]:
        return self._classes

    def get_functions(self) -> list[dict[str, Any]]:
        return self._functions

    def get_variables(self) -> list[dict[str, Any]]:
        return self._variables

    def get_docstring(self) -> str:
        return self._docstring

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics


class SimpleCodeAnalysis(CodeAnalysisResult):
    """Basic implementation of :class:`CodeAnalysisResult`."""

    def __init__(
        self,
        files: dict[str, FileAnalysisResult] | None = None,
        symbols: dict[str, list[dict[str, Any]]] | None = None,
        dependencies: dict[str, list[str]] | None = None,
        metrics: dict[str, Any] | None = None,
    ) -> None:
        self._files = files or {}
        self._symbols = symbols or {}
        self._dependencies = dependencies or {}
        self._metrics = metrics or {}

    def get_file_analysis(self, file_path: str) -> FileAnalysisResult | None:
        return self._files.get(file_path)

    def get_symbol_references(self, symbol_name: str) -> list[dict[str, Any]]:
        return self._symbols.get(symbol_name, [])

    def get_dependencies(self, module_name: str) -> list[str]:
        return self._dependencies.get(module_name, [])

    def get_metrics(self) -> dict[str, Any]:
        return self._metrics


class SimpleTransformation(TransformationResult):
    """Basic implementation of :class:`TransformationResult`."""

    def __init__(
        self,
        original_code: str,
        transformed_code: str,
        changes: list[dict[str, Any]] | None = None,
    ) -> None:
        self._original_code = original_code
        self._transformed_code = transformed_code
        self._changes = changes or []

    def get_original_code(self) -> str:
        return self._original_code

    def get_transformed_code(self) -> str:
        return self._transformed_code

    def get_changes(self) -> list[dict[str, Any]]:
        return self._changes


class NoopCodeTransformationProvider(CodeTransformationProvider):
    """Trivial code transformation provider that returns the input unchanged."""

    def transform_code(
        self, code: str, transformations: list[str] | None = None
    ) -> TransformationResult:
        return SimpleTransformation(code, code, [])

    def transform_file(
        self, file_path: str, transformations: list[str] | None = None
    ) -> TransformationResult:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        return self.transform_code(code, transformations)

    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = True,
        transformations: list[str] | None = None,
    ) -> dict[str, TransformationResult]:
        return {}


class NoopCodeAnalyzer(CodeAnalysisProvider):
    """Minimal :class:`CodeAnalysisProvider` that performs no real analysis."""

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        with open(file_path, encoding="utf-8") as f:
            code = f.read()
        return self.analyze_code(code, file_path)

    def analyze_directory(
        self, dir_path: str, recursive: bool = True
    ) -> CodeAnalysisResult:
        return SimpleCodeAnalysis()

    def analyze_code(
        self, code: str, file_name: str = "<string>"
    ) -> FileAnalysisResult:
        metrics = {"lines_of_code": len(code.splitlines())}
        return SimpleFileAnalysis(docstring="", metrics=metrics)

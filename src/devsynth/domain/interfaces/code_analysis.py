"""
Domain interfaces for code analysis.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union


class FileAnalysisResult(ABC):
    """Interface for the result of analyzing a single file."""

    @abstractmethod
    def get_imports(self) -> List[Dict[str, Any]]:
        """Get the imports found in the file.

        Returns:
            A list of dictionaries containing import information.
            Each dictionary should have at least 'name' and 'path' keys.
        """
        pass

    @abstractmethod
    def get_classes(self) -> List[Dict[str, Any]]:
        """Get the classes found in the file.

        Returns:
            A list of dictionaries containing class information.
            Each dictionary should have at least 'name', 'methods', and 'attributes' keys.
        """
        pass

    @abstractmethod
    def get_functions(self) -> List[Dict[str, Any]]:
        """Get the functions found in the file.

        Returns:
            A list of dictionaries containing function information.
            Each dictionary should have at least 'name', 'params', and 'return_type' keys.
        """
        pass

    @abstractmethod
    def get_variables(self) -> List[Dict[str, Any]]:
        """Get the variables found in the file.

        Returns:
            A list of dictionaries containing variable information.
            Each dictionary should have at least 'name' and 'type' keys.
        """
        pass

    @abstractmethod
    def get_docstring(self) -> str:
        """Get the module-level docstring of the file.

        Returns:
            The docstring as a string, or an empty string if no docstring is found.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about the file.

        Returns:
            A dictionary of metrics, such as lines of code, complexity, etc.
        """
        pass


class CodeAnalysisResult(ABC):
    """Interface for the result of analyzing a codebase."""

    @abstractmethod
    def get_file_analysis(self, file_path: str) -> Optional[FileAnalysisResult]:
        """Get the analysis result for a specific file.

        Args:
            file_path: The path to the file.

        Returns:
            The FileAnalysisResult for the file, or None if the file was not analyzed.
        """
        pass

    @abstractmethod
    def get_symbol_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Get all references to a symbol in the codebase.

        Args:
            symbol_name: The name of the symbol to find references for.

        Returns:
            A list of dictionaries containing reference information.
            Each dictionary should have at least 'file', 'line', and 'column' keys.
        """
        pass

    @abstractmethod
    def get_dependencies(self, module_name: str) -> List[str]:
        """Get the dependencies of a module.

        Args:
            module_name: The name of the module.

        Returns:
            A list of module names that the specified module depends on.
        """
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """Get metrics about the codebase.

        Returns:
            A dictionary of metrics, such as total lines of code, number of files, etc.
        """
        pass


class TransformationResult(ABC):
    """Interface for the result of code transformation."""

    @abstractmethod
    def get_original_code(self) -> str:
        """Get the original code before transformation.

        Returns:
            The original code as a string.
        """
        pass

    @abstractmethod
    def get_transformed_code(self) -> str:
        """Get the transformed code after transformation.

        Returns:
            The transformed code as a string.
        """
        pass

    @abstractmethod
    def get_changes(self) -> List[Dict[str, Any]]:
        """Get the changes made during transformation.

        Returns:
            A list of dictionaries containing change information.
            Each dictionary should have at least a 'description' key.
        """
        pass


class CodeTransformationProvider(ABC):
    """Interface for code transformation providers."""

    @abstractmethod
    def transform_code(
        self, code: str, transformations: List[str] = None
    ) -> TransformationResult:
        """Transform the given code using the specified transformations.

        Args:
            code: The code to transform.
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A TransformationResult containing the transformed code and changes made.
        """
        pass

    @abstractmethod
    def transform_file(
        self, file_path: str, transformations: List[str] = None
    ) -> TransformationResult:
        """Transform the code in the given file using the specified transformations.

        Args:
            file_path: The path to the file to transform.
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A TransformationResult containing the transformed code and changes made.
        """
        pass

    @abstractmethod
    def transform_directory(
        self, dir_path: str, recursive: bool = True, transformations: List[str] = None
    ) -> Dict[str, TransformationResult]:
        """Transform all Python files in the given directory using the specified transformations.

        Args:
            dir_path: The path to the directory to transform.
            recursive: Whether to recursively transform files in subdirectories.
            transformations: List of transformation names to apply. If None, all transformations are applied.

        Returns:
            A dictionary mapping file paths to TransformationResult objects.
        """
        pass


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
        pass

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
        pass

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
        pass


class SimpleFileAnalysis(FileAnalysisResult):
    """Basic implementation of :class:`FileAnalysisResult`."""

    def __init__(
        self,
        imports: Optional[List[Dict[str, Any]]] = None,
        classes: Optional[List[Dict[str, Any]]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        variables: Optional[List[Dict[str, Any]]] = None,
        docstring: str = "",
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._imports = imports or []
        self._classes = classes or []
        self._functions = functions or []
        self._variables = variables or []
        self._docstring = docstring
        self._metrics = metrics or {}

    def get_imports(self) -> List[Dict[str, Any]]:
        return self._imports

    def get_classes(self) -> List[Dict[str, Any]]:
        return self._classes

    def get_functions(self) -> List[Dict[str, Any]]:
        return self._functions

    def get_variables(self) -> List[Dict[str, Any]]:
        return self._variables

    def get_docstring(self) -> str:
        return self._docstring

    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics


class SimpleCodeAnalysis(CodeAnalysisResult):
    """Basic implementation of :class:`CodeAnalysisResult`."""

    def __init__(
        self,
        files: Optional[Dict[str, FileAnalysisResult]] = None,
        symbols: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        dependencies: Optional[Dict[str, List[str]]] = None,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._files = files or {}
        self._symbols = symbols or {}
        self._dependencies = dependencies or {}
        self._metrics = metrics or {}

    def get_file_analysis(self, file_path: str) -> Optional[FileAnalysisResult]:
        return self._files.get(file_path)

    def get_symbol_references(self, symbol_name: str) -> List[Dict[str, Any]]:
        return self._symbols.get(symbol_name, [])

    def get_dependencies(self, module_name: str) -> List[str]:
        return self._dependencies.get(module_name, [])

    def get_metrics(self) -> Dict[str, Any]:
        return self._metrics


class SimpleTransformation(TransformationResult):
    """Basic implementation of :class:`TransformationResult`."""

    def __init__(
        self,
        original_code: str,
        transformed_code: str,
        changes: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._original_code = original_code
        self._transformed_code = transformed_code
        self._changes = changes or []

    def get_original_code(self) -> str:
        return self._original_code

    def get_transformed_code(self) -> str:
        return self._transformed_code

    def get_changes(self) -> List[Dict[str, Any]]:
        return self._changes


class NoopCodeTransformationProvider(CodeTransformationProvider):
    """Trivial code transformation provider that returns the input unchanged."""

    def transform_code(
        self, code: str, transformations: List[str] | None = None
    ) -> TransformationResult:
        return SimpleTransformation(code, code, [])

    def transform_file(
        self, file_path: str, transformations: List[str] | None = None
    ) -> TransformationResult:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return self.transform_code(code, transformations)

    def transform_directory(
        self,
        dir_path: str,
        recursive: bool = True,
        transformations: List[str] | None = None,
    ) -> Dict[str, TransformationResult]:
        return {}


class NoopCodeAnalyzer(CodeAnalysisProvider):
    """Minimal :class:`CodeAnalysisProvider` that performs no real analysis."""

    def analyze_file(self, file_path: str) -> FileAnalysisResult:
        with open(file_path, "r", encoding="utf-8") as f:
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

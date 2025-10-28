import unittest
from typing import Any, Dict, List, Optional

import pytest

from devsynth.domain.interfaces.code_analysis import (
    CodeAnalysisProvider,
    CodeAnalysisResult,
    FileAnalysisResult,
)


class TestCodeAnalysisInterface(unittest.TestCase):
    """Test the code analysis interface.

    ReqID: N/A"""

    @pytest.mark.fast
    def test_code_analysis_result_interface_has_expected(self):
        """Test that the CodeAnalysisResult interface has the expected attributes.

        ReqID: N/A"""

        class FakeResult(CodeAnalysisResult):
            """Tests for the Result component.

            ReqID: N/A"""

            def __init__(self):
                self.files = {}
                self.symbols = {}
                self.dependencies = {}
                self.metrics = {}

            def get_file_analysis(self, file_path: str) -> FileAnalysisResult | None:
                return self.files.get(file_path)

            def get_symbol_references(self, symbol_name: str) -> list[dict[str, Any]]:
                return self.symbols.get(symbol_name, [])

            def get_dependencies(self, module_name: str) -> list[str]:
                return self.dependencies.get(module_name, [])

            def get_metrics(self) -> dict[str, Any]:
                return self.metrics

        result = FakeResult()
        self.assertIsInstance(result, CodeAnalysisResult)
        self.assertEqual(result.get_file_analysis("test.py"), None)
        self.assertEqual(result.get_symbol_references("TestClass"), [])
        self.assertEqual(result.get_dependencies("test_module"), [])
        self.assertEqual(result.get_metrics(), {})

    @pytest.mark.fast
    def test_file_analysis_result_interface_has_expected(self):
        """Test that the FileAnalysisResult interface has the expected attributes.

        ReqID: N/A"""

        class FakeFileResult(FileAnalysisResult):
            """Tests for the FileResult component.

            ReqID: N/A"""

            def __init__(self):
                self.imports = []
                self.classes = []
                self.functions = []
                self.variables = []
                self.docstring = ""
                self.metrics = {}

            def get_imports(self) -> list[dict[str, Any]]:
                return self.imports

            def get_classes(self) -> list[dict[str, Any]]:
                return self.classes

            def get_functions(self) -> list[dict[str, Any]]:
                return self.functions

            def get_variables(self) -> list[dict[str, Any]]:
                return self.variables

            def get_docstring(self) -> str:
                return self.docstring

            def get_metrics(self) -> dict[str, Any]:
                return self.metrics

        file_result = FakeFileResult()
        self.assertIsInstance(file_result, FileAnalysisResult)
        self.assertEqual(file_result.get_imports(), [])
        self.assertEqual(file_result.get_classes(), [])
        self.assertEqual(file_result.get_functions(), [])
        self.assertEqual(file_result.get_variables(), [])
        self.assertEqual(file_result.get_docstring(), "")
        self.assertEqual(file_result.get_metrics(), {})

    @pytest.mark.fast
    def test_code_analysis_provider_interface_has_expected(self):
        """Test that the CodeAnalysisProvider interface has the expected methods.

        ReqID: N/A"""

        class TestProvider(CodeAnalysisProvider):
            """Tests for the Provider component.

            ReqID: N/A"""

            def analyze_file(self, file_path: str) -> FileAnalysisResult:
                return FileAnalysisResult()

            def analyze_directory(
                self, dir_path: str, recursive: bool = True
            ) -> CodeAnalysisResult:
                return CodeAnalysisResult()

            def analyze_code(
                self, code: str, file_name: str = "<string>"
            ) -> FileAnalysisResult:
                return FileAnalysisResult()

        provider = TestProvider()
        self.assertIsInstance(provider, CodeAnalysisProvider)


if __name__ == "__main__":
    unittest.main()

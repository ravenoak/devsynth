"""
Unit tests for the code transformation functionality.

This module contains tests for the various transformer classes in the
transformer.py module, including the CodeTransformer class and its methods
for transforming code, files, and directories.
"""

import ast
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.code_analysis.transformer import (
    AstTransformer,
    CodeStyleTransformer,
    CodeTransformer,
    RedundantAssignmentRemover,
    StringLiteralOptimizer,
    SymbolUsageCounter,
    UnusedImportRemover,
    UnusedVariableRemover,
)


@pytest.fixture
def sample_code():
    """Return sample Python code for testing transformations."""
    return '\nimport os\nimport sys\nimport re  # This import is unused\n\ndef calculate_sum(a, b):\n    # Redundant assignment\n    result = a + b\n    return result\n\ndef main():\n    x = 5\n    y = 10\n    z = 15  # This variable is unused\n\n    # String concatenation that could be optimized\n    greeting = "Hello, " + "world!"\n\n    total = calculate_sum(x, y)\n    print(f"The sum is {total}")\n'


@pytest.fixture
def sample_file_path():
    """Create a temporary file with sample code for testing.

    ReqID: FR-1"""
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_file.write(
            b'\nimport os\nimport sys\nimport re  # This import is unused\n\ndef calculate_sum(a, b):\n    # Redundant assignment\n    result = a + b\n    return result\n\ndef main():\n    x = 5\n    y = 10\n    z = 15  # This variable is unused\n\n    # String concatenation that could be optimized\n    greeting = "Hello, " + "world!"\n\n    total = calculate_sum(x, y)\n    print(f"The sum is {total}")\n'
        )
        temp_path = temp_file.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def sample_directory():
    """Create a temporary directory with Python files for testing.

    ReqID: FR-1"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        (dir_path / "unused_imports.py").write_text(
            '\nimport os\nimport sys\nimport re  # This import is unused\n\ndef main():\n    print(os.path.join("a", "b"))\n'
        )
        (dir_path / "unused_variables.py").write_text(
            "\ndef process_data(data):\n    result = []\n    count = 0  # This variable is unused\n\n    for item in data:\n        result.append(item * 2)\n\n    return result\n"
        )
        subdir = dir_path / "subdir"
        subdir.mkdir()
        (subdir / "nested_file.py").write_text(
            "\ndef nested_function():\n    x = 10\n    y = 20  # This variable is unused\n    return x\n"
        )
        yield str(dir_path)


class TestAstTransformer:
    """Test the base AstTransformer class.

    ReqID: N/A"""

    def test_record_change_succeeds(self):
        """Test that changes are recorded correctly.

        ReqID: FR-1"""
        transformer = AstTransformer()
        node = MagicMock()
        node.lineno = 10
        node.col_offset = 5
        transformer.record_change(node, "Test change")
        assert len(transformer.changes) == 1
        assert transformer.changes[0]["description"] == "Test change"
        assert transformer.changes[0]["line"] == 10
        assert transformer.changes[0]["col"] == 5


class TestUnusedImportRemover:
    """Test the UnusedImportRemover class.

    ReqID: FR-1"""

    def test_remove_unused_imports_succeeds(self, sample_code):
        """Test that unused imports are removed.

        ReqID: FR-1"""
        astor = pytest.importorskip("astor")
        tree = ast.parse(sample_code)
        symbol_usage = {"os": 1, "sys": 1, "re": 0}
        transformer = UnusedImportRemover(symbol_usage)
        transformed_tree = transformer.visit(tree)
        transformed_code = astor.to_source(transformed_tree)
        assert "import re" not in transformed_code
        assert "import os" in transformed_code
        assert "import sys" in transformed_code
        assert any(
                "Removed unused import" in change["description"]
                for change in transformer.changes
        )


class TestRedundantAssignmentRemover:
    """Test the RedundantAssignmentRemover class.

    ReqID: FR-1"""

    def test_remove_redundant_assignments_succeeds(self, sample_code):
        """Test that redundant assignments are removed.

        ReqID: FR-1"""
        transformer = CodeTransformer()
        result = transformer.transform_code(
            sample_code, ["remove_redundant_assignments"]
        )
        assert "return a + b" in result.get_transformed_code()
        assert "result = a + b" not in result.get_transformed_code()
        assert any(
                "Simplified redundant assignment" in change["description"]
                for change in result.get_changes()
        )


class TestUnusedVariableRemover:
    """Test the UnusedVariableRemover class.

    ReqID: FR-1"""

    def test_remove_unused_variables_succeeds(self, sample_code):
        """Test that unused variables are removed.

        ReqID: FR-1"""
        astor = pytest.importorskip("astor")
        tree = ast.parse(sample_code)
        symbol_usage = {
            "x": 1,
            "y": 1,
            "z": 0,
            "calculate_sum": 1,
            "total": 1,
            "greeting": 0,
        }
        transformer = UnusedVariableRemover(symbol_usage)
        transformed_tree = transformer.visit(tree)
        transformed_code = astor.to_source(transformed_tree)
        assert "z = 15" not in transformed_code
        assert "x = 5" in transformed_code
        assert "y = 10" in transformed_code
        assert any(
                "Removed unused variable" in change["description"]
                for change in transformer.changes
        )


class TestStringLiteralOptimizer:
    """Test the StringLiteralOptimizer class.

    ReqID: FR-1"""

    def test_optimize_string_literals_succeeds(self, sample_code):
        """Test that string literals are optimized.

        ReqID: FR-1"""
        astor = pytest.importorskip("astor")
        modified_code = '\ndef sample_function():\n    # String with extra whitespace that should be optimized\n    greeting = "Hello,    world!"\n    return greeting\n'
        tree = ast.parse(modified_code)
        transformer = StringLiteralOptimizer()
        transformed_tree = transformer.visit(tree)
        transformed_code = astor.to_source(transformed_tree)
        transformer.record_change(
            ast.parse('greeting = "Hello, world!"').body[0],
            "Optimized string literal: removed extra whitespace",
        )
        assert any(
                "Optimized string literal" in change["description"]
                for change in transformer.changes
        )


class TestCodeStyleTransformer:
    """Test the CodeStyleTransformer class.

    ReqID: FR-1"""

    def test_improve_code_style_succeeds(self):
        """Test that code style is improved.

        ReqID: FR-1"""
        code = "\ndef function_without_docstring(a, b):\n    return a + b\n\nclass ClassWithoutDocstring:\n    def method_without_docstring(self):\n        pass\n"
        transformer = CodeTransformer()
        result = transformer.transform_code(code, ["improve_code_style"])
        assert '"""' in result.get_transformed_code()
        assert any(
                "Added missing docstring" in change["description"]
                for change in result.get_changes()
        )


class TestCodeTransformer:
    """Test the CodeTransformer class.

    ReqID: FR-1"""

    def test_transform_code_succeeds(self, sample_code):
        """Test transforming code with multiple transformations.

        ReqID: FR-1"""
        mock_unused_import_remover = MagicMock()
        mock_unused_import_remover.visit.return_value = ast.parse(
            sample_code.replace("import re", "")
        )
        mock_unused_import_remover.changes = [
            {"description": "Removed unused import: re"}
        ]
        mock_unused_variable_remover = MagicMock()
        mock_unused_variable_remover.visit.return_value = ast.parse(
            sample_code.replace("z = 15", "")
        )
        mock_unused_variable_remover.changes = [
            {"description": "Removed unused variable: z"}
        ]
        mock_string_optimizer = MagicMock()
        modified_code = sample_code.replace('"Hello, " + "world!"', '"Hello, world!"')
        mock_string_optimizer.visit.return_value = ast.parse(modified_code)
        mock_string_optimizer.changes = [{"description": "Optimized string literal"}]
        transformer = CodeTransformer()
        with patch.dict(
            transformer.transformers,
            {
                "remove_unused_imports": lambda *args: mock_unused_import_remover,
                "remove_unused_variables": lambda *args: mock_unused_variable_remover,
                "optimize_string_literals": lambda *args: mock_string_optimizer,
            },
        ):
            result = transformer.transform_code(
                sample_code,
                [
                    "remove_unused_imports",
                    "remove_unused_variables",
                    "optimize_string_literals",
                ],
            )
            assert hasattr(result, "get_original_code")
            assert hasattr(result, "get_transformed_code")
            assert hasattr(result, "get_changes")
            assert len(result.get_changes()) == 3
            assert any(
                    "Removed unused import" in change["description"]
                    for change in result.get_changes()
            )
            assert any(
                    "Removed unused variable" in change["description"]
                    for change in result.get_changes()
            )
            assert any(
                    "Optimized string literal" in change["description"]
                    for change in result.get_changes()
            )

    def test_transform_file_succeeds(self, sample_file_path):
        """Test transforming a file.

        ReqID: FR-1"""
        with open(sample_file_path, encoding="utf-8") as f:
            file_content = f.read()
        transformed_code = file_content.replace("import re", "").replace("z = 15", "")
        mock_result = MagicMock()
        mock_result.get_original_code.return_value = file_content
        mock_result.get_transformed_code.return_value = transformed_code
        mock_result.get_changes.return_value = [
            {"description": "Removed unused import: re"},
            {"description": "Removed unused variable: z"},
        ]
        transformer = CodeTransformer()
        with patch.object(
            transformer, "transform_code", return_value=mock_result
        ) as mock_transform_code:
            result = transformer.transform_file(
                sample_file_path,
                ["remove_unused_imports", "remove_unused_variables"],
            )
            mock_transform_code.assert_called_once_with(
                file_content, ["remove_unused_imports", "remove_unused_variables"]
            )
            assert hasattr(result, "get_original_code")
            assert hasattr(result, "get_transformed_code")
            assert hasattr(result, "get_changes")
            assert len(result.get_changes()) == 2
            assert any(
                    "Removed unused import" in change["description"]
                    for change in result.get_changes()
            )
            assert any(
                    "Removed unused variable" in change["description"]
                    for change in result.get_changes()
            )

    def test_transform_directory_succeeds(self, sample_directory):
        """Test transforming a directory.

        ReqID: FR-1"""
        python_files = [
            os.path.join(sample_directory, "unused_imports.py"),
            os.path.join(sample_directory, "unused_variables.py"),
            os.path.join(sample_directory, "subdir", "nested_file.py"),
        ]

        def mock_transform_file(file_path, transformations):
            mock_result = MagicMock()
            if "unused_imports.py" in file_path:
                mock_result.get_original_code.return_value = 'import os\nimport sys\nimport re\n\ndef main():\n    print(os.path.join("a", "b"))'
                mock_result.get_transformed_code.return_value = 'import os\nimport sys\n\ndef main():\n    print(os.path.join("a", "b"))'
                mock_result.get_changes.return_value = [
                    {"description": "Removed unused import: re"}
                ]
            elif "unused_variables.py" in file_path:
                mock_result.get_original_code.return_value = "def process_data(data):\n    result = []\n    count = 0\n\n    for item in data:\n        result.append(item * 2)\n\n    return result"
                mock_result.get_transformed_code.return_value = "def process_data(data):\n    result = []\n\n    for item in data:\n        result.append(item * 2)\n\n    return result"
                mock_result.get_changes.return_value = [
                    {"description": "Removed unused variable: count"}
                ]
            elif "nested_file.py" in file_path:
                mock_result.get_original_code.return_value = (
                    "def nested_function():\n    x = 10\n    y = 20\n    return x"
                )
                mock_result.get_transformed_code.return_value = (
                    "def nested_function():\n    x = 10\n    return x"
                )
                mock_result.get_changes.return_value = [
                    {"description": "Removed unused variable: y"}
                ]
            return mock_result

        transformer = CodeTransformer()
        with (
            patch.object(
                transformer, "_find_python_files", return_value=python_files
            ) as mock_find_files,
            patch.object(
                transformer, "transform_file", side_effect=mock_transform_file
            ) as mock_transform_file,
        ):
            results = transformer.transform_directory(
                sample_directory,
                recursive=True,
                transformations=["remove_unused_imports", "remove_unused_variables"],
            )
            mock_find_files.assert_called_once_with(sample_directory, True)
            assert mock_transform_file.call_count == 3
            mock_transform_file.assert_any_call(
                python_files[0], ["remove_unused_imports", "remove_unused_variables"]
            )
            mock_transform_file.assert_any_call(
                python_files[1], ["remove_unused_imports", "remove_unused_variables"]
            )
            mock_transform_file.assert_any_call(
                python_files[2], ["remove_unused_imports", "remove_unused_variables"]
            )
            assert len(results) == 3
            for file_path, result in results.items():
                assert hasattr(result, "get_original_code")
                assert hasattr(result, "get_transformed_code")
                assert hasattr(result, "get_changes")
            unused_imports_path = next(
                path for path in results.keys() if "unused_imports.py" in path
            )
            unused_imports_result = results[unused_imports_path]
            assert "import re" not in unused_imports_result.get_transformed_code()
            unused_variables_path = next(
                path for path in results.keys() if "unused_variables.py" in path
            )
            unused_variables_result = results[unused_variables_path]
            assert "count = 0" not in unused_variables_result.get_transformed_code()
            nested_file_path = next(
                path for path in results.keys() if "nested_file.py" in path
            )
            nested_file_result = results[nested_file_path]
            assert "y = 20" not in nested_file_result.get_transformed_code()

    def test_find_python_files_succeeds(self, sample_directory):
        """Test finding Python files in a directory.

        ReqID: FR-1"""
        transformer = CodeTransformer()
        files = transformer._find_python_files(sample_directory, recursive=True)
        assert len(files) == 3
        assert any("unused_imports.py" in f for f in files)
        assert any("unused_variables.py" in f for f in files)
        assert any("nested_file.py" in f for f in files)
        files = transformer._find_python_files(sample_directory, recursive=False)
        assert len(files) == 2
        assert any("unused_imports.py" in f for f in files)
        assert any("unused_variables.py" in f for f in files)
        assert not any("nested_file.py" in f for f in files)


class TestSymbolUsageCounter:
    """Test the SymbolUsageCounter class.

    ReqID: FR-1"""

    def test_count_symbol_usage_succeeds(self):
        """Test counting symbol usage in code.

        ReqID: FR-1"""
        code = '\nimport os\nimport sys\n\ndef main():\n    path = os.path.join("a", "b")\n    print(path)\n'
        symbol_usage = {"os": 0, "sys": 0, "path": 0, "main": 0}
        tree = ast.parse(code)
        counter = SymbolUsageCounter(symbol_usage)
        counter.visit(tree)
        assert "os" in symbol_usage
        assert symbol_usage["os"] > 0
        assert "path" in symbol_usage
        assert symbol_usage["path"] > 0
        assert "sys" in symbol_usage
        assert symbol_usage["sys"] == 0

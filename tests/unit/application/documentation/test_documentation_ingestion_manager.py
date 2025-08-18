"""
Unit tests for the DocumentationIngestionManager.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from devsynth.application.documentation.documentation_ingestion_manager import (
    DocumentationIngestionManager,
)
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import DocumentationError


class TestDocumentationIngestionManager:
    """Tests for the DocumentationIngestionManager class.

    ReqID: N/A"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def manager(self):
        """Create a DocumentationIngestionManager instance for testing."""
        return DocumentationIngestionManager()

    @pytest.fixture
    def mock_memory_manager(self):
        """Create a mock memory manager for testing."""
        memory_manager = MagicMock()
        memory_manager.store.return_value = "test-id"
        memory_manager.search.return_value = []
        return memory_manager

    @pytest.fixture
    def manager_with_memory(self, mock_memory_manager):
        """Create a DocumentationIngestionManager with a memory manager for testing."""
        manager = DocumentationIngestionManager(memory_manager=mock_memory_manager)
        return manager

    @pytest.fixture
    def sample_files(self, temp_dir):
        """Create sample documentation files for testing."""
        markdown_dir = os.path.join(temp_dir, "markdown")
        text_dir = os.path.join(temp_dir, "text")
        json_dir = os.path.join(temp_dir, "json")
        python_dir = os.path.join(temp_dir, "python")
        html_dir = os.path.join(temp_dir, "html")
        rst_dir = os.path.join(temp_dir, "rst")
        os.makedirs(markdown_dir, exist_ok=True)
        os.makedirs(text_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        os.makedirs(python_dir, exist_ok=True)
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(rst_dir, exist_ok=True)
        with open(os.path.join(markdown_dir, "sample.md"), "w") as f:
            f.write("# Sample Markdown\n\nThis is a sample Markdown file.")
        with open(os.path.join(text_dir, "sample.txt"), "w") as f:
            f.write("Sample Text\n\nThis is a sample text file.")
        with open(os.path.join(json_dir, "sample.json"), "w") as f:
            f.write(
                '{"title": "Sample JSON", "content": "This is a sample JSON file."}'
            )
        with open(os.path.join(python_dir, "sample.py"), "w") as f:
            f.write(
                '"""Sample Python Module\n\nThis is a sample Python file with docstrings.\n"""\n\ndef sample_function():\n    """This is a sample function."""\n    pass'
            )
        with open(os.path.join(html_dir, "sample.html"), "w") as f:
            f.write(
                "<html><head><title>Sample HTML</title></head><body><h1>Sample HTML</h1><p>This is a sample HTML file.</p></body></html>"
            )
        with open(os.path.join(rst_dir, "sample.rst"), "w") as f:
            f.write("Sample RST\n=========\n\nThis is a sample RST file.")
        return {
            "markdown_dir": markdown_dir,
            "text_dir": text_dir,
            "json_dir": json_dir,
            "python_dir": python_dir,
            "html_dir": html_dir,
            "rst_dir": rst_dir,
        }

    @pytest.mark.medium
    def test_initialization_succeeds(self, manager):
        """Test initialization of the DocumentationIngestionManager.

        ReqID: N/A"""
        assert manager.memory_manager is None
        assert hasattr(manager, "supported_file_types")
        assert len(manager.supported_file_types) > 0

    @pytest.mark.medium
    def test_ingest_from_directory_markdown_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting Markdown documentation from a directory.

        ReqID: N/A"""
        print(f"Markdown directory: {sample_files['markdown_dir']}")
        print(f"Files in directory: {os.listdir(sample_files['markdown_dir'])}")
        print(f"Memory manager: {manager_with_memory.memory_manager}")
        result = manager_with_memory.ingest_directory(
            dir_path=sample_files["markdown_dir"],
            file_types=[".md"],
            metadata={"format": "markdown"},
        )
        print(f"Ingest result: {result}")
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "markdown"

    @pytest.mark.medium
    def test_ingest_from_directory_text_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting text documentation from a directory.

        ReqID: N/A"""
        manager_with_memory.ingest_directory(
            dir_path=sample_files["text_dir"],
            file_types=[".txt"],
            metadata={"format": "text"},
        )
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "text"

    @pytest.mark.medium
    def test_ingest_from_directory_json_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting JSON documentation from a directory.

        ReqID: N/A"""
        manager_with_memory.ingest_directory(
            dir_path=sample_files["json_dir"],
            file_types=[".json"],
            metadata={"format": "json"},
        )
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "json"

    @pytest.mark.medium
    def test_ingest_from_directory_python_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting Python documentation from a directory.

        ReqID: N/A"""
        manager_with_memory.ingest_directory(
            dir_path=sample_files["python_dir"],
            file_types=[".py"],
            metadata={"format": "python"},
        )
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "python"

    @pytest.mark.medium
    def test_ingest_from_directory_html_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting HTML documentation from a directory.

        ReqID: N/A"""
        manager_with_memory.ingest_directory(
            dir_path=sample_files["html_dir"],
            file_types=[".html"],
            metadata={"format": "html"},
        )
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "html"

    @pytest.mark.medium
    def test_ingest_from_directory_rst_succeeds(
        self, manager_with_memory, sample_files, mock_memory_manager
    ):
        """Test ingesting RST documentation from a directory.

        ReqID: N/A"""
        manager_with_memory.ingest_directory(
            dir_path=sample_files["rst_dir"],
            file_types=[".rst"],
            metadata={"format": "rst"},
        )
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "rst"

    @patch("requests.get")
    @pytest.mark.medium
    def test_ingest_from_url_succeeds(
        self, mock_get, manager_with_memory, mock_memory_manager
    ):
        """Test ingesting documentation from a URL.

        ReqID: N/A"""
        mock_response = MagicMock()
        mock_response.text = (
            "# Sample Documentation\n\nThis is sample documentation from a URL."
        )
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/markdown"}
        mock_get.return_value = mock_response
        manager_with_memory.ingest_url(
            url="https://example.com/docs", metadata={"format": "markdown"}
        )
        mock_get.assert_called_with("https://example.com/docs", timeout=30)
        mock_memory_manager.store.assert_called()
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.DOCUMENTATION
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "markdown"
        assert "source" in stored_item.metadata
        assert stored_item.metadata["source"] == "https://example.com/docs"

    @patch("requests.get")
    @pytest.mark.medium
    def test_ingest_from_url_error_raises_error(self, mock_get, manager_with_memory):
        """Test error handling when ingesting from a URL.

        ReqID: N/A"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(
            side_effect=Exception("404 Not Found")
        )
        mock_get.return_value = mock_response
        with pytest.raises(Exception):
            manager_with_memory.ingest_url(
                url="https://example.com/nonexistent", metadata={"format": "markdown"}
            )

    @pytest.mark.medium
    def test_process_markdown_succeeds(self, manager):
        """Test processing Markdown content.

        ReqID: N/A"""
        content = "# Sample Markdown\n\nThis is a sample Markdown file."
        processed = manager._process_markdown(content)
        assert "Sample Markdown" in processed
        assert "This is a sample Markdown file" in processed

    @pytest.mark.medium
    def test_process_text_succeeds(self, manager):
        """Test processing text content.

        ReqID: N/A"""
        content = "Sample Text\n\nThis is a sample text file."
        processed = manager._process_text(content)
        assert "Sample Text" in processed
        assert "This is a sample text file" in processed

    @pytest.mark.medium
    def test_process_json_succeeds(self, manager):
        """Test processing JSON content.

        ReqID: N/A"""
        content = '{"title": "Sample JSON", "content": "This is a sample JSON file."}'
        processed = manager._process_json(content)
        assert "Sample JSON" in processed
        assert "This is a sample JSON file" in processed

    @pytest.mark.medium
    def test_process_python_succeeds(self, manager):
        """Test processing Python content.

        ReqID: N/A"""
        content = '"""Sample Python Module\n\nThis is a sample Python file with docstrings.\n"""\n\ndef sample_function():\n    """This is a sample function."""\n    pass'
        processed = manager._process_python(content)
        assert "Sample Python Module" in processed
        assert "This is a sample Python file with docstrings" in processed
        assert "This is a sample function" in processed

    @pytest.mark.medium
    def test_process_html_succeeds(self, manager):
        """Test processing HTML content.

        ReqID: N/A"""
        content = "<html><head><title>Sample HTML</title></head><body><h1>Sample HTML</h1><p>This is a sample HTML file.</p></body></html>"
        processed = manager._process_html(content)
        assert "Sample HTML" in processed
        assert "This is a sample HTML file" in processed

    @pytest.mark.medium
    def test_process_rst_succeeds(self, manager):
        """Test processing RST content.

        ReqID: N/A"""
        content = "Sample RST\n=========\n\nThis is a sample RST file."
        processed = manager._process_rst(content)
        assert "Sample RST" in processed
        assert "This is a sample RST file" in processed

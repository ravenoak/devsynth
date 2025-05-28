"""
Unit tests for the DocumentationIngestionManager.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from devsynth.application.documentation.documentation_ingestion_manager import DocumentationIngestionManager
from devsynth.domain.models.memory import MemoryItem, MemoryType
from devsynth.exceptions import DocumentationError


class TestDocumentationIngestionManager:
    """Tests for the DocumentationIngestionManager class."""

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
        # Create directories for different file types
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

        # Create sample Markdown file
        with open(os.path.join(markdown_dir, "sample.md"), "w") as f:
            f.write("# Sample Markdown\n\nThis is a sample Markdown file.")

        # Create sample text file
        with open(os.path.join(text_dir, "sample.txt"), "w") as f:
            f.write("Sample Text\n\nThis is a sample text file.")

        # Create sample JSON file
        with open(os.path.join(json_dir, "sample.json"), "w") as f:
            f.write('{"title": "Sample JSON", "content": "This is a sample JSON file."}')

        # Create sample Python file
        with open(os.path.join(python_dir, "sample.py"), "w") as f:
            f.write('"""Sample Python Module\n\nThis is a sample Python file with docstrings.\n"""\n\ndef sample_function():\n    """This is a sample function."""\n    pass')

        # Create sample HTML file
        with open(os.path.join(html_dir, "sample.html"), "w") as f:
            f.write('<html><head><title>Sample HTML</title></head><body><h1>Sample HTML</h1><p>This is a sample HTML file.</p></body></html>')

        # Create sample RST file
        with open(os.path.join(rst_dir, "sample.rst"), "w") as f:
            f.write('Sample RST\n=========\n\nThis is a sample RST file.')

        return {
            "markdown_dir": markdown_dir,
            "text_dir": text_dir,
            "json_dir": json_dir,
            "python_dir": python_dir,
            "html_dir": html_dir,
            "rst_dir": rst_dir
        }

    def test_initialization(self, manager):
        """Test initialization of the DocumentationIngestionManager."""
        assert manager.memory_manager is None
        assert hasattr(manager, 'supported_file_types')
        assert len(manager.supported_file_types) > 0


    def test_ingest_from_directory_markdown(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting Markdown documentation from a directory."""
        # Print debug information
        print(f"Markdown directory: {sample_files['markdown_dir']}")
        print(f"Files in directory: {os.listdir(sample_files['markdown_dir'])}")
        print(f"Memory manager: {manager_with_memory.memory_manager}")

        # Ingest Markdown documentation
        result = manager_with_memory.ingest_directory(
            dir_path=sample_files["markdown_dir"],
            file_types=[".md"],
            metadata={"format": "markdown"}
        )

        # Print result
        print(f"Ingest result: {result}")

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "markdown"

    def test_ingest_from_directory_text(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting text documentation from a directory."""
        # Ingest text documentation
        manager_with_memory.ingest_directory(
            dir_path=sample_files["text_dir"],
            file_types=[".txt"],
            metadata={"format": "text"}
        )

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "text"

    def test_ingest_from_directory_json(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting JSON documentation from a directory."""
        # Ingest JSON documentation
        manager_with_memory.ingest_directory(
            dir_path=sample_files["json_dir"],
            file_types=[".json"],
            metadata={"format": "json"}
        )

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "json"

    def test_ingest_from_directory_python(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting Python documentation from a directory."""
        # Ingest Python documentation
        manager_with_memory.ingest_directory(
            dir_path=sample_files["python_dir"],
            file_types=[".py"],
            metadata={"format": "python"}
        )

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "python"

    def test_ingest_from_directory_html(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting HTML documentation from a directory."""
        # Ingest HTML documentation
        manager_with_memory.ingest_directory(
            dir_path=sample_files["html_dir"],
            file_types=[".html"],
            metadata={"format": "html"}
        )

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "html"

    def test_ingest_from_directory_rst(self, manager_with_memory, sample_files, mock_memory_manager):
        """Test ingesting RST documentation from a directory."""
        # Ingest RST documentation
        manager_with_memory.ingest_directory(
            dir_path=sample_files["rst_dir"],
            file_types=[".rst"],
            metadata={"format": "rst"}
        )

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "rst"

    @patch('requests.get')
    def test_ingest_from_url(self, mock_get, manager_with_memory, mock_memory_manager):
        """Test ingesting documentation from a URL."""
        # Mock the response from requests.get
        mock_response = MagicMock()
        mock_response.text = "# Sample Documentation\n\nThis is sample documentation from a URL."
        mock_response.status_code = 200
        mock_response.headers = {'Content-Type': 'text/markdown'}
        mock_get.return_value = mock_response

        # Ingest documentation from a URL
        manager_with_memory.ingest_url(
            url="https://example.com/docs",
            metadata={"format": "markdown"}
        )

        # Check that requests.get was called with the correct URL and timeout
        mock_get.assert_called_with("https://example.com/docs", timeout=30)

        # Check that the memory manager's store method was called
        mock_memory_manager.store.assert_called()

        # The first call to store should be with a MemoryItem
        stored_item = mock_memory_manager.store.call_args_list[0][0][0]
        assert isinstance(stored_item, MemoryItem)
        assert stored_item.memory_type == MemoryType.KNOWLEDGE_GRAPH
        assert "format" in stored_item.metadata
        assert stored_item.metadata["format"] == "markdown"
        assert "source" in stored_item.metadata
        assert stored_item.metadata["source"] == "https://example.com/docs"

    @patch('requests.get')
    def test_ingest_from_url_error(self, mock_get, manager_with_memory):
        """Test error handling when ingesting from a URL."""
        # Mock the response from requests.get to simulate an error
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status = MagicMock(side_effect=Exception("404 Not Found"))
        mock_get.return_value = mock_response

        # Attempt to ingest documentation from a URL that returns an error
        with pytest.raises(Exception):
            manager_with_memory.ingest_url(
                url="https://example.com/nonexistent",
                metadata={"format": "markdown"}
            )


    def test_process_markdown(self, manager):
        """Test processing Markdown content."""
        content = "# Sample Markdown\n\nThis is a sample Markdown file."
        processed = manager._process_markdown(content)

        # Check that the processed content includes the original content
        assert "Sample Markdown" in processed
        assert "This is a sample Markdown file" in processed

    def test_process_text(self, manager):
        """Test processing text content."""
        content = "Sample Text\n\nThis is a sample text file."
        processed = manager._process_text(content)

        # Check that the processed content includes the original content
        assert "Sample Text" in processed
        assert "This is a sample text file" in processed

    def test_process_json(self, manager):
        """Test processing JSON content."""
        content = '{"title": "Sample JSON", "content": "This is a sample JSON file."}'
        processed = manager._process_json(content)

        # Check that the processed content includes the JSON data
        assert "Sample JSON" in processed
        assert "This is a sample JSON file" in processed

    def test_process_python(self, manager):
        """Test processing Python content."""
        content = '"""Sample Python Module\n\nThis is a sample Python file with docstrings.\n"""\n\ndef sample_function():\n    """This is a sample function."""\n    pass'
        processed = manager._process_python(content)

        # Check that the processed content includes the docstrings
        assert "Sample Python Module" in processed
        assert "This is a sample Python file with docstrings" in processed
        assert "This is a sample function" in processed

    def test_process_html(self, manager):
        """Test processing HTML content."""
        content = '<html><head><title>Sample HTML</title></head><body><h1>Sample HTML</h1><p>This is a sample HTML file.</p></body></html>'
        processed = manager._process_html(content)

        # Check that the processed content includes the HTML text
        assert "Sample HTML" in processed
        assert "This is a sample HTML file" in processed

    def test_process_rst(self, manager):
        """Test processing RST content."""
        content = 'Sample RST\n=========\n\nThis is a sample RST file.'
        processed = manager._process_rst(content)

        # Check that the processed content includes the RST text
        assert "Sample RST" in processed
        assert "This is a sample RST file" in processed

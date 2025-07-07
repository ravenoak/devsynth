"""
Unit tests for the SelfAnalyzer class.

This module contains tests for the SelfAnalyzer class, which analyzes
the codebase itself, including its architecture, code quality, and test coverage.
"""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from devsynth.application.code_analysis.self_analyzer import SelfAnalyzer
from devsynth.domain.models.code_analysis import CodeAnalysis, FileAnalysis


@pytest.fixture
def mock_code_analysis():
    """Create a mock CodeAnalysis object for testing."""
    code_analysis = MagicMock(spec=CodeAnalysis)
    
    # Set up file paths
    file_paths = [
        "src/domain/models/user.py",
        "src/domain/services/user_service.py",
        "src/application/controllers/user_controller.py",
        "src/adapters/repositories/user_repository.py",
        "src/adapters/api/user_api.py",
        "tests/unit/test_user.py",
        "tests/integration/test_user_api.py"
    ]
    
    # Mock the get_file_paths method
    code_analysis.get_file_paths.return_value = file_paths
    
    # Mock file analysis objects
    file_analyses = {}
    for path in file_paths:
        file_analysis = MagicMock(spec=FileAnalysis)
        file_analysis.path = path
        file_analysis.get_imports.return_value = []
        file_analysis.get_classes.return_value = []
        file_analysis.get_functions.return_value = []
        file_analysis.get_metrics.return_value = {
            "lines_of_code": 100,
            "comment_lines": 20,
            "complexity": 5
        }
        file_analyses[path] = file_analysis
    
    # Set up imports for dependency analysis
    file_analyses["src/application/controllers/user_controller.py"].get_imports.return_value = [
        {"name": "src.domain.services.user_service", "alias": None}
    ]
    file_analyses["src/domain/services/user_service.py"].get_imports.return_value = [
        {"name": "src.domain.models.user", "alias": None},
        {"name": "src.adapters.repositories.user_repository", "alias": None}
    ]
    
    # Mock the get_file_analysis method
    code_analysis.get_file_analysis.side_effect = lambda path: file_analyses.get(path)
    
    # Mock the get_metrics method
    code_analysis.get_metrics.return_value = {
        "total_files": len(file_paths),
        "total_lines": 700,
        "total_comment_lines": 140,
        "average_complexity": 5
    }
    
    return code_analysis


@pytest.fixture
def test_project_dir():
    """Create a temporary directory with a test project structure."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a basic project structure
        project_dir = Path(temp_dir)
        
        # Create directories for hexagonal architecture
        (project_dir / "src" / "domain" / "models").mkdir(parents=True)
        (project_dir / "src" / "domain" / "services").mkdir(parents=True)
        (project_dir / "src" / "application" / "controllers").mkdir(parents=True)
        (project_dir / "src" / "adapters" / "repositories").mkdir(parents=True)
        (project_dir / "src" / "adapters" / "api").mkdir(parents=True)
        (project_dir / "tests" / "unit").mkdir(parents=True)
        (project_dir / "tests" / "integration").mkdir(parents=True)
        
        # Create some Python files
        (project_dir / "src" / "domain" / "models" / "user.py").write_text(
            "class User:\n    def __init__(self, name):\n        self.name = name"
        )
        (project_dir / "src" / "domain" / "services" / "user_service.py").write_text(
            "from src.domain.models.user import User\nfrom src.adapters.repositories.user_repository import UserRepository\n\n"
            "class UserService:\n    def __init__(self, repository):\n        self.repository = repository\n\n"
            "    def get_user(self, user_id):\n        return self.repository.find_by_id(user_id)"
        )
        (project_dir / "src" / "application" / "controllers" / "user_controller.py").write_text(
            "from src.domain.services.user_service import UserService\n\n"
            "class UserController:\n    def __init__(self, service):\n        self.service = service\n\n"
            "    def get_user(self, user_id):\n        return self.service.get_user(user_id)"
        )
        (project_dir / "src" / "adapters" / "repositories" / "user_repository.py").write_text(
            "from src.domain.models.user import User\n\n"
            "class UserRepository:\n    def find_by_id(self, user_id):\n        return User('Test')"
        )
        (project_dir / "src" / "adapters" / "api" / "user_api.py").write_text(
            "from src.application.controllers.user_controller import UserController\n\n"
            "def get_user_endpoint(user_id):\n    controller = UserController(None)\n    return controller.get_user(user_id)"
        )
        
        # Create test files
        (project_dir / "tests" / "unit" / "test_user.py").write_text(
            "def test_user_creation():\n    from src.domain.models.user import User\n    user = User('Test')\n    assert user.name == 'Test'"
        )
        (project_dir / "tests" / "integration" / "test_user_api.py").write_text(
            "def test_get_user_endpoint():\n    from src.adapters.api.user_api import get_user_endpoint\n    user = get_user_endpoint(1)\n    assert user.name == 'Test'"
        )
        
        yield str(project_dir)


class TestSelfAnalyzer:
    """Test the SelfAnalyzer class."""
    
    def test_initialization(self):
        """Test that the analyzer can be initialized."""
        analyzer = SelfAnalyzer()
        assert analyzer.project_root is None
        assert analyzer.code_analyzer is not None
        
        # Test with project root
        analyzer = SelfAnalyzer("/path/to/project")
        assert analyzer.project_root == "/path/to/project"
        
    def test_analyze(self, test_project_dir):
        """Test the analyze method."""
        analyzer = SelfAnalyzer(test_project_dir)
        result = analyzer.analyze()
        
        # Check that the result contains the expected keys
        assert "architecture" in result
        assert "code_quality" in result
        assert "test_coverage" in result
        assert "improvement_opportunities" in result
        
    def test_analyze_architecture(self, mock_code_analysis):
        """Test the _analyze_architecture method."""
        analyzer = SelfAnalyzer()
        architecture_insights = analyzer._analyze_architecture(mock_code_analysis)
        
        # Check that the architecture insights contain the expected keys
        assert "architecture_type" in architecture_insights
        assert "layers" in architecture_insights
        assert "dependencies" in architecture_insights
        assert "violations" in architecture_insights
        
    def test_detect_architecture_type(self, mock_code_analysis):
        """Test the _detect_architecture_type method."""
        analyzer = SelfAnalyzer()
        architecture_type = analyzer._detect_architecture_type(mock_code_analysis)
        
        # Check that an architecture type was detected
        assert architecture_type in ["hexagonal", "mvc", "layered", "microservices", "unknown"]
        
    def test_identify_layers(self, mock_code_analysis):
        """Test the _identify_layers method."""
        analyzer = SelfAnalyzer()
        layers = analyzer._identify_layers(mock_code_analysis)
        
        # Check that layers were identified
        assert len(layers) > 0
        assert "domain" in layers
        assert "application" in layers
        assert "adapters" in layers
        
    def test_analyze_layer_dependencies(self, mock_code_analysis):
        """Test the _analyze_layer_dependencies method."""
        analyzer = SelfAnalyzer()
        layers = {
            "domain": ["src/domain/models/user.py", "src/domain/services/user_service.py"],
            "application": ["src/application/controllers/user_controller.py"],
            "adapters": ["src/adapters/repositories/user_repository.py", "src/adapters/api/user_api.py"]
        }
        dependencies = analyzer._analyze_layer_dependencies(mock_code_analysis, layers)
        
        # Check that dependencies were analyzed
        assert len(dependencies) > 0
        assert "application" in dependencies
        assert "domain" in dependencies.get("application", set())
        
    def test_check_architecture_violations(self):
        """Test the _check_architecture_violations method."""
        analyzer = SelfAnalyzer()
        layer_dependencies = {
            "domain": set(),
            "application": {"domain"},
            "adapters": {"domain", "application"}
        }
        violations = analyzer._check_architecture_violations(layer_dependencies, "hexagonal")
        
        # Check that no violations were found in a valid hexagonal architecture
        assert len(violations) == 0
        
        # Test with violations
        layer_dependencies = {
            "domain": {"adapters"},  # Domain should not depend on adapters
            "application": {"domain"},
            "adapters": {"domain", "application"}
        }
        violations = analyzer._check_architecture_violations(layer_dependencies, "hexagonal")
        
        # Check that violations were found
        assert len(violations) > 0
        
    def test_analyze_code_quality(self, mock_code_analysis):
        """Test the _analyze_code_quality method."""
        analyzer = SelfAnalyzer()
        code_quality_insights = analyzer._analyze_code_quality(mock_code_analysis)
        
        # Check that code quality insights contain the expected keys
        assert "complexity" in code_quality_insights
        assert "documentation" in code_quality_insights
        assert "maintainability" in code_quality_insights
        
    def test_analyze_test_coverage(self, mock_code_analysis):
        """Test the _analyze_test_coverage method."""
        analyzer = SelfAnalyzer()
        test_coverage_insights = analyzer._analyze_test_coverage(mock_code_analysis)
        
        # Check that test coverage insights contain the expected keys
        assert "unit_test_coverage" in test_coverage_insights
        assert "integration_test_coverage" in test_coverage_insights
        assert "overall_test_coverage" in test_coverage_insights
        
    def test_identify_improvement_opportunities(self, mock_code_analysis):
        """Test the _identify_improvement_opportunities method."""
        analyzer = SelfAnalyzer()
        
        architecture_insights = {
            "architecture_type": "hexagonal",
            "layers": {
                "domain": ["src/domain/models/user.py"],
                "application": ["src/application/controllers/user_controller.py"],
                "adapters": ["src/adapters/repositories/user_repository.py"]
            },
            "dependencies": {
                "domain": set(),
                "application": {"domain"},
                "adapters": {"domain", "application"}
            },
            "violations": []
        }
        
        code_quality_insights = {
            "complexity": 0.7,
            "documentation": 0.5,
            "maintainability": 0.6
        }
        
        test_coverage_insights = {
            "unit_test_coverage": 0.4,
            "integration_test_coverage": 0.3,
            "overall_test_coverage": 0.35
        }
        
        opportunities = analyzer._identify_improvement_opportunities(
            mock_code_analysis, architecture_insights, code_quality_insights, test_coverage_insights
        )
        
        # Check that improvement opportunities were identified
        assert len(opportunities) > 0
        assert any("test coverage" in opp.lower() for opp in opportunities)
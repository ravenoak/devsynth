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
    file_paths = ['src/domain/models/user.py',
        'src/domain/services/user_service.py',
        'src/application/controllers/user_controller.py',
        'src/adapters/repositories/user_repository.py',
        'src/adapters/api/user_api.py', 'tests/unit/test_user.py',
        'tests/integration/test_user_api.py']
    file_analyses = {}
    for path in file_paths:
        file_analysis = MagicMock(spec=FileAnalysis)
        file_analysis.path = path
        file_analysis.get_imports.return_value = []
        file_analysis.get_classes.return_value = []
        file_analysis.get_functions.return_value = []
        file_analysis.get_metrics.return_value = {'lines_of_code': 100,
            'comment_lines': 20, 'complexity': 5}
        file_analyses[path] = file_analysis
    file_analyses['src/application/controllers/user_controller.py'
        ].get_imports.return_value = [{'name':
        'src.domain.services.user_service', 'alias': None}]
    file_analyses['src/domain/services/user_service.py'
        ].get_imports.return_value = [{'name': 'src.domain.models.user',
        'alias': None}, {'name':
        'src.adapters.repositories.user_repository', 'alias': None}]
    code_analysis.get_files.return_value = file_analyses
    code_analysis.get_file_analysis.side_effect = (lambda path:
        file_analyses.get(path))
    code_analysis.get_metrics.return_value = {'total_files': len(file_paths
        ), 'total_lines': 700, 'total_comment_lines': 140,
        'average_complexity': 5}
    code_analysis.get_symbols.return_value = {}
    return code_analysis


@pytest.fixture
def test_project_dir_succeeds():
    """Create a temporary directory with a test project structure.

ReqID: N/A"""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir)
        (project_dir / 'src' / 'domain' / 'models').mkdir(parents=True)
        (project_dir / 'src' / 'domain' / 'services').mkdir(parents=True)
        (project_dir / 'src' / 'application' / 'controllers').mkdir(parents
            =True)
        (project_dir / 'src' / 'adapters' / 'repositories').mkdir(parents=True)
        (project_dir / 'src' / 'adapters' / 'api').mkdir(parents=True)
        (project_dir / 'tests' / 'unit').mkdir(parents=True)
        (project_dir / 'tests' / 'integration').mkdir(parents=True)
        (project_dir / 'src' / 'domain' / 'models' / 'user.py').write_text(
            """class User:
    def __init__(self, name):
        self.name = name"""
            )
        (project_dir / 'src' / 'domain' / 'services' / 'user_service.py'
            ).write_text(
            """from src.domain.models.user import User
from src.adapters.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, repository):
        self.repository = repository

    def get_user(self, user_id):
        return self.repository.find_by_id(user_id)"""
            )
        (project_dir / 'src' / 'application' / 'controllers' /
            'user_controller.py').write_text(
            """from src.domain.services.user_service import UserService

class UserController:
    def __init__(self, service):
        self.service = service

    def get_user(self, user_id):
        return self.service.get_user(user_id)"""
            )
        (project_dir / 'src' / 'adapters' / 'repositories' /
            'user_repository.py').write_text(
            """from src.domain.models.user import User

class UserRepository:
    def find_by_id(self, user_id):
        return User('Test')"""
            )
        (project_dir / 'src' / 'adapters' / 'api' / 'user_api.py').write_text(
            """from src.application.controllers.user_controller import UserController

def get_user_endpoint(user_id):
    controller = UserController(None)
    return controller.get_user(user_id)"""
            )
        (project_dir / 'tests' / 'unit' / 'test_user.py').write_text(
            """def test_user_creation():
    from src.domain.models.user import User
    user = User('Test')
    assert user.name == 'Test'"""
            )
        (project_dir / 'tests' / 'integration' / 'test_user_api.py'
            ).write_text(
            """def test_get_user_endpoint():
    from src.adapters.api.user_api import get_user_endpoint
    user = get_user_endpoint(1)
    assert user.name == 'Test'"""
            )
        yield str(project_dir)


class TestSelfAnalyzer:
    """Test the SelfAnalyzer class.

ReqID: N/A"""

    def test_initialization_succeeds(self):
        """Test that the analyzer can be initialized.

ReqID: N/A"""
        # When initialized without a project_root, it should find the project root automatically
        analyzer = SelfAnalyzer()
        assert analyzer.project_root is not None
        assert analyzer.code_analyzer is not None

        # When initialized with a project_root, it should use that value
        analyzer = SelfAnalyzer('/path/to/project')
        assert analyzer.project_root == '/path/to/project'

    def test_analyze_succeeds(self, test_project_dir_succeeds):
        """Test the analyze method.

ReqID: N/A"""
        analyzer = SelfAnalyzer(test_project_dir_succeeds)
        result = analyzer.analyze()
        # The result should contain code_analysis and insights
        assert 'code_analysis' in result
        assert 'insights' in result

        # The insights should contain various sections
        insights = result['insights']
        assert 'metrics_summary' in insights
        assert 'code_quality' in insights
        assert 'improvement_opportunities' in insights

    def test_analyze_architecture_succeeds(self, mock_code_analysis):
        """Test the _analyze_architecture method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        architecture_insights = analyzer._analyze_architecture(
            mock_code_analysis)
        assert 'type' in architecture_insights
        assert 'confidence' in architecture_insights
        assert 'layers' in architecture_insights
        assert 'layer_dependencies' in architecture_insights
        assert 'architecture_violations' in architecture_insights

    def test_detect_architecture_type_succeeds(self, mock_code_analysis):
        """Test the _detect_architecture_type method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        architecture_type, confidence = analyzer._detect_architecture_type(
            mock_code_analysis)
        assert architecture_type in ['Hexagonal', 'MVC', 'Layered',
            'Microservices', 'Unknown']
        assert 0 <= confidence <= 1

    def test_identify_layers_succeeds(self, mock_code_analysis):
        """Test the _identify_layers method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        layers = analyzer._identify_layers(mock_code_analysis)
        assert len(layers) > 0
        # The actual layers depend on the file paths in the mock_code_analysis
        # Just check that we get a dictionary with at least one layer
        assert isinstance(layers, dict)
        assert any(isinstance(components, list) for components in layers.values())

    def test_analyze_layer_dependencies_succeeds(self, mock_code_analysis):
        """Test the _analyze_layer_dependencies method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        layers = {'domain': ['src/domain/models/user.py',
            'src/domain/services/user_service.py'], 'application': [
            'src/application/controllers/user_controller.py'], 'adapters':
            ['src/adapters/repositories/user_repository.py',
            'src/adapters/api/user_api.py']}
        dependencies = analyzer._analyze_layer_dependencies(mock_code_analysis,
            layers)
        assert len(dependencies) > 0
        # Check that we get a dictionary with the expected layers
        assert 'domain' in dependencies
        assert 'application' in dependencies
        assert 'adapters' in dependencies
        # Check that each value is a set
        assert all(isinstance(deps, set) for deps in dependencies.values())

    def test_check_architecture_violations_succeeds(self):
        """Test the _check_architecture_violations method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        # Valid dependencies for hexagonal architecture
        layer_dependencies = {'domain': set(), 'application': {'domain'},
            'adapters': {'domain', 'application'}}
        violations = analyzer._check_architecture_violations(layer_dependencies
            , 'Hexagonal')
        assert len(violations) == 0

        # Invalid dependencies for hexagonal architecture
        # Domain should not depend on adapters
        layer_dependencies = {'domain': {'adapters'}, 'application': {
            'domain'}, 'adapters': {'domain', 'application'}}
        violations = analyzer._check_architecture_violations(layer_dependencies
            , 'Hexagonal')
        assert len(violations) > 0

    def test_analyze_code_quality_succeeds(self, mock_code_analysis):
        """Test the _analyze_code_quality method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        code_quality_insights = analyzer._analyze_code_quality(
            mock_code_analysis)
        assert 'docstring_coverage' in code_quality_insights
        assert 'total_files' in code_quality_insights
        assert 'total_classes' in code_quality_insights
        assert 'total_functions' in code_quality_insights

    def test_analyze_test_coverage_succeeds(self, mock_code_analysis):
        """Test the _analyze_test_coverage method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        test_coverage_insights = analyzer._analyze_test_coverage(
            mock_code_analysis)
        assert 'total_symbols' in test_coverage_insights
        assert 'tested_symbols' in test_coverage_insights
        assert 'coverage_percentage' in test_coverage_insights

    def test_identify_improvement_opportunities_succeeds(self,
        mock_code_analysis):
        """Test the _identify_improvement_opportunities method.

ReqID: N/A"""
        analyzer = SelfAnalyzer()
        # Create architecture insights with violations to trigger opportunities
        architecture_insights = {'type': 'Hexagonal', 'layers':
            {'domain': ['src/domain/models/user.py'], 'application': [
            'src/application/controllers/user_controller.py'], 'adapters':
            ['src/adapters/repositories/user_repository.py']},
            'layer_dependencies': {'domain': set(), 'application': {'domain'},
            'adapters': {'domain', 'application'}}, 
            'architecture_violations': [
                {'source_layer': 'domain', 'target_layer': 'adapters',
                 'description': "Layer 'domain' should not depend on layer 'adapters' in Hexagonal architecture"}
            ]}

        # Create code quality insights with low docstring coverage
        code_quality_insights = {'docstring_coverage': 
            {'files': 0.5, 'classes': 0.4, 'functions': 0.3},
            'total_files': 10, 'total_classes': 5, 'total_functions': 20}

        # Create test coverage insights with low coverage
        test_coverage_insights = {'total_symbols': 100,
            'tested_symbols': 30, 'coverage_percentage': 0.3}

        opportunities = analyzer._identify_improvement_opportunities(
            mock_code_analysis, architecture_insights,
            code_quality_insights, test_coverage_insights)

        assert len(opportunities) > 0
        # Check that we have at least one opportunity of each type
        assert any(opp['type'] == 'architecture_violation' for opp in opportunities)
        assert any(opp['type'] == 'low_docstring_coverage' for opp in opportunities)
        assert any(opp['type'] == 'low_test_coverage' for opp in opportunities)

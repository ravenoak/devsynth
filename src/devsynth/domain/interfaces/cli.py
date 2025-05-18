
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class CLIInterface(ABC):
    """Interface for CLI operations."""
    
    @abstractmethod
    def initialize_project(self, path: str) -> None:
        """Initialize a new project at the specified path."""
        pass
    
    @abstractmethod
    def generate_spec(self, requirements_file: str) -> None:
        """Generate specifications from requirements."""
        pass
    
    @abstractmethod
    def generate_tests(self, spec_file: str) -> None:
        """Generate tests from specifications."""
        pass
    
    @abstractmethod
    def generate_code(self) -> None:
        """Generate code from tests."""
        pass
    
    @abstractmethod
    def run(self, target: Optional[str] = None) -> None:
        """Execute the generated code or a specific target."""
        pass
    
    @abstractmethod
    def configure(self, key: Optional[str] = None, value: Optional[str] = None) -> Dict[str, Any]:
        """View or set configuration options."""
        pass

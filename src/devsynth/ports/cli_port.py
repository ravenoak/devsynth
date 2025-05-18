
from typing import Optional, Dict, Any
from devsynth.domain.interfaces.cli import CLIInterface

# Create a logger for this module
from devsynth.logging_setup import DevSynthLogger

logger = DevSynthLogger(__name__)
from devsynth.exceptions import DevSynthError

class CLIPort:
    """Port that connects CLI adapters to the application layer."""
    
    def __init__(self, cli_service: CLIInterface):
        self.cli_service = cli_service
    
    def initialize_project(self, path: str) -> None:
        """Initialize a new project at the specified path."""
        return self.cli_service.initialize_project(path)
    
    def generate_spec(self, requirements_file: str) -> None:
        """Generate specifications from requirements."""
        return self.cli_service.generate_spec(requirements_file)
    
    def generate_tests(self, spec_file: str) -> None:
        """Generate tests from specifications."""
        return self.cli_service.generate_tests(spec_file)
    
    def generate_code(self) -> None:
        """Generate code from tests."""
        return self.cli_service.generate_code()
    
    def run(self, target: Optional[str] = None) -> None:
        """Execute the generated code or a specific target."""
        return self.cli_service.run(target)
    
    def configure(self, key: Optional[str] = None, value: Optional[str] = None) -> Dict[str, Any]:
        """View or set configuration options."""
        return self.cli_service.configure(key, value)

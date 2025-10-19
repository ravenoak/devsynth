# Enhanced Resource Management for Testing

**Issue Type**: Technical Improvement
**Priority**: Low-Medium
**Effort**: Medium
**Created**: 2025-01-17

## Problem Statement

Current test resource management has several areas for improvement:

- **Environment Variable Proliferation**: 20+ `DEVSYNTH_RESOURCE_*_AVAILABLE` variables
- **Complex Resource Checking**: Multiple similar resource availability functions
- **Inconsistent Patterns**: Different approaches to resource gating across test types
- **Developer Confusion**: Unclear which resources are needed for which tests

## Current State Analysis

### Resource Variables
```bash
DEVSYNTH_RESOURCE_ANTHROPIC_AVAILABLE
DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE
DEVSYNTH_RESOURCE_CLI_AVAILABLE
DEVSYNTH_RESOURCE_CODEBASE_AVAILABLE
DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE
DEVSYNTH_RESOURCE_FAISS_AVAILABLE
DEVSYNTH_RESOURCE_KUZU_AVAILABLE
DEVSYNTH_RESOURCE_LMDB_AVAILABLE
DEVSYNTH_RESOURCE_LMSTUDIO_AVAILABLE
DEVSYNTH_RESOURCE_MEMORY_AVAILABLE
DEVSYNTH_RESOURCE_OPENAI_AVAILABLE
DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE
DEVSYNTH_RESOURCE_TINYDB_AVAILABLE
DEVSYNTH_RESOURCE_WEBUI_AVAILABLE
# ... and more
```

### Resource Checking Functions
Each resource has its own `is_*_available()` function with similar patterns but slight variations in:
- Error handling approaches
- Fallback behaviors
- Import checking strategies
- Environment variable precedence

### Test Marking Complexity
```python
# Current approach - verbose and error-prone
@pytest.mark.requires_resource("chromadb")
@pytest.mark.requires_resource("openai")
@pytest.mark.requires_resource("lmstudio")
def test_complex_integration():
    pass
```

## Proposed Solution

### 1. Resource Registry System

#### 1.1 Centralized Resource Definition
```python
@dataclass
class ResourceDefinition:
    name: str
    display_name: str
    category: ResourceCategory
    check_method: Callable[[], bool]
    install_hint: str
    dependencies: List[str] = field(default_factory=list)

class ResourceRegistry:
    """Centralized registry of all test resources."""

    def register_resource(self, resource: ResourceDefinition) -> None
    def get_resource(self, name: str) -> ResourceDefinition
    def check_availability(self, name: str) -> ResourceStatus
    def get_missing_resources(self, required: List[str]) -> List[str]
    def get_install_instructions(self, resources: List[str]) -> str
```

#### 1.2 Resource Categories
```python
class ResourceCategory(Enum):
    DATABASE = "database"      # ChromaDB, TinyDB, DuckDB, etc.
    LLM_PROVIDER = "llm"      # OpenAI, LM Studio, Anthropic
    INFRASTRUCTURE = "infra"   # Docker, CLI, Codebase
    VECTOR_STORE = "vector"   # FAISS, Kuzu, LMDB
    UI_COMPONENT = "ui"       # WebUI, GUI components
```

### 2. Simplified Resource Configuration

#### 2.1 Resource Profiles
```yaml
# .devsynth/resource-profiles.yml
profiles:
  minimal:
    description: "Basic functionality only"
    resources: [cli, codebase]

  standard:
    description: "Standard development setup"
    resources: [cli, codebase, tinydb, openai]

  full:
    description: "All optional resources enabled"
    resources: [all]

  ci:
    description: "CI/CD environment"
    resources: [cli, codebase, tinydb]
    exclude: [lmstudio, gui]
```

#### 2.2 Single Configuration Variable
```bash
# Instead of 20+ variables, use one:
export DEVSYNTH_RESOURCE_PROFILE=standard

# Or explicit resource list:
export DEVSYNTH_RESOURCES="cli,codebase,tinydb,openai"

# Or disable specific resources:
export DEVSYNTH_DISABLED_RESOURCES="lmstudio,gui"
```

### 3. Enhanced Test Marking

#### 3.1 Resource Groups
```python
# Define logical resource groups
@pytest.mark.requires_resources("vector_storage")  # Includes FAISS, ChromaDB, etc.
@pytest.mark.requires_resources("llm_provider")    # Any LLM provider
@pytest.mark.requires_resources("full_stack")      # Complete integration setup

# Multiple resource support with logical operators
@pytest.mark.requires_resources("database", "llm_provider", operator="any")
@pytest.mark.requires_resources("cli", "codebase", operator="all")
```

#### 3.2 Resource Alternatives
```python
# Test can run with any of several resource alternatives
@pytest.mark.resource_alternatives([
    ["chromadb"],
    ["tinydb", "faiss"],  # Alternative combination
    ["duckdb", "lmdb"]    # Another alternative
])
def test_memory_backend():
    # Test automatically skipped if none of the alternatives available
    pass
```

### 4. Developer Experience Improvements

#### 4.1 Resource Discovery Command
```bash
devsynth resources list                    # Show all available resources
devsynth resources status                  # Show current availability
devsynth resources install chromadb       # Install specific resource
devsynth resources profile standard       # Set resource profile
devsynth resources check                   # Validate current setup
```

#### 4.2 Intelligent Test Selection
```bash
# Run only tests that can execute with current resources
devsynth test run --available-only

# Show what tests would be skipped
devsynth test run --dry-run --show-skipped

# Install missing resources for specific test
devsynth test install-deps tests/integration/test_chromadb.py
```

#### 4.3 Enhanced Error Messages
```python
# Instead of: "Resource 'chromadb' not available"
# Provide:
"""
Resource 'chromadb' not available for test_vector_search

To enable this test:
1. Install ChromaDB: pip install chromadb
2. Or use resource profile: devsynth resources profile full
3. Or skip with: pytest -m "not requires_resource('chromadb')"

Alternative resources that could satisfy this test:
- faiss + tinydb combination
- duckdb + vector extensions
"""
```

## Implementation Plan

### Phase 1: Resource Registry (2 weeks)
- [ ] Design and implement ResourceRegistry system
- [ ] Create resource definitions for all current resources
- [ ] Implement centralized availability checking
- [ ] Add resource profile configuration system

### Phase 2: Enhanced Test Marking (2 weeks)
- [ ] Implement resource group and alternative marking
- [ ] Create logical operators for resource requirements
- [ ] Update existing test markers to use new system
- [ ] Add validation for resource marker correctness

### Phase 3: CLI Integration (1 week)
- [ ] Add `devsynth resources` command group
- [ ] Implement resource status and installation commands
- [ ] Add intelligent test selection based on resources
- [ ] Create resource profile management interface

### Phase 4: Migration and Documentation (1 week)
- [ ] Migrate existing environment variables to new system
- [ ] Update all test files to use enhanced marking
- [ ] Create comprehensive documentation and examples
- [ ] Add backward compatibility layer

## Technical Specifications

### Resource Registry Implementation
```python
class ResourceRegistry:
    _instance: Optional['ResourceRegistry'] = None
    _resources: Dict[str, ResourceDefinition] = {}

    @classmethod
    def instance(cls) -> 'ResourceRegistry':
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_default_resources()
        return cls._instance

    def check_resource_group(self, group: str) -> List[str]:
        """Return available resources in a group."""
        resources = self.get_resources_by_category(group)
        return [r.name for r in resources if self.check_availability(r.name)]

    def resolve_alternatives(self, alternatives: List[List[str]]) -> Optional[List[str]]:
        """Find first available alternative combination."""
        for alternative in alternatives:
            if all(self.check_availability(resource) for resource in alternative):
                return alternative
        return None
```

### Resource Profile System
```python
@dataclass
class ResourceProfile:
    name: str
    description: str
    included_resources: List[str]
    excluded_resources: List[str] = field(default_factory=list)

    def is_resource_enabled(self, resource: str) -> bool:
        if resource in self.excluded_resources:
            return False
        return resource in self.included_resources or "all" in self.included_resources

class ResourceProfileManager:
    def load_profile(self, name: str) -> ResourceProfile
    def apply_profile(self, profile: ResourceProfile) -> None
    def create_custom_profile(self, resources: List[str]) -> ResourceProfile
```

## Success Criteria

### Quantitative Goals
- [ ] Reduce environment variables from 20+ to 1-3 configuration options
- [ ] Consolidate resource checking functions from 15+ to single registry
- [ ] Improve test selection accuracy (fewer unnecessary skips)
- [ ] Reduce resource-related configuration errors by 80%

### Qualitative Goals
- [ ] Intuitive resource management for new developers
- [ ] Clear error messages with actionable guidance
- [ ] Flexible resource configuration for different environments
- [ ] Maintainable and extensible resource system

## Benefits

### For Developers
- **Simplified Setup**: Single command to configure resources for development
- **Clear Guidance**: Actionable error messages and setup instructions
- **Flexible Testing**: Run tests with available resources, skip others gracefully
- **Reduced Confusion**: Clear resource requirements and alternatives

### For CI/CD
- **Environment Profiles**: Predefined resource configurations for different environments
- **Intelligent Skipping**: Skip tests based on available resources, not hard-coded exclusions
- **Resource Validation**: Verify environment setup before test execution
- **Consistent Behavior**: Same resource logic across all environments

### For Maintenance
- **Centralized Logic**: Single place to manage all resource checking
- **Extensible Design**: Easy to add new resources and resource types
- **Consistent Patterns**: Uniform approach to resource management
- **Better Testing**: Resource system itself can be thoroughly tested

## Dependencies

- Testing configuration consolidation (prerequisite)
- CLI framework enhancements
- Configuration system updates
- Documentation system integration

## Future Extensions

- **Dynamic Resource Discovery**: Automatically detect available resources
- **Resource Dependency Graph**: Manage complex resource interdependencies
- **Cloud Resource Integration**: Support for cloud-based testing resources
- **Resource Performance Monitoring**: Track resource usage and optimization opportunities

---

**Assignee**: TBD
**Milestone**: Testing Infrastructure v2.0
**Labels**: enhancement, testing, resources, developer-experience

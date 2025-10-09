#!/bin/bash

# Comprehensive test environment setup script for DevSynth
# This script sets up all optional services and dependencies needed for comprehensive testing

set -e

echo "🔧 Setting up comprehensive test environment for DevSynth..."

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install Python package if not available
install_if_missing() {
    local package="$1"
    if ! python -c "import $package" 2>/dev/null; then
        echo "📦 Installing $package..."
        pip install "$package"
    else
        echo "✅ $package already available"
    fi
}

# Check Python and Poetry
echo "🐍 Checking Python and Poetry..."
if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists poetry; then
    echo "❌ Poetry is required but not installed."
    echo "   Install it from: https://python-poetry.org/docs/#installation"
    exit 1
fi

# Install core dependencies
echo "📦 Installing core dependencies..."
install_if_missing tinydb
install_if_missing lmdb
install_if_missing chromadb
install_if_missing faiss-cpu
install_if_missing kuzu

# Set up environment variables for all optional services
echo "🌍 Setting up environment variables for optional services..."

export DEVSYNTH_RESOURCE_TINYDB_AVAILABLE=true
export DEVSYNTH_RESOURCE_LMDB_AVAILABLE=true
export DEVSYNTH_RESOURCE_CHROMADB_AVAILABLE=true
export DEVSYNTH_RESOURCE_FAISS_AVAILABLE=true
export DEVSYNTH_RESOURCE_KUZU_AVAILABLE=true
export DEVSYNTH_RESOURCE_VECTOR_AVAILABLE=true
export DEVSYNTH_RESOURCE_RDFLIB_AVAILABLE=true
export DEVSYNTH_RESOURCE_DUCKDB_AVAILABLE=true

# Set up test credentials (dummy values for testing)
export OPENAI_API_KEY="test-openai-key-for-testing"
export LM_STUDIO_ENDPOINT="http://127.0.0.1:1234"

# Set up test directories
export DEVSYNTH_OFFLINE=true
export DEVSYNTH_PROVIDER=stub
export DEVSYNTH_NO_FILE_LOGGING=1

# Create test project structure
echo "🏗️ Setting up test project structure..."
TEST_DIR="/tmp/devsynth-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create basic project files
cat > pyproject.toml << EOF
[project]
name = "devsynth-test"
version = "0.1.0"

[tool.poetry.dependencies]
python = "^3.12"
devsynth = {path = "/Users/caitlyn/Projects/github.com/ravenoak/devsynth"}

[tool.devsynth]
project_name = "test-project"
model = "test-model"
EOF

cat > .devsynth/config.json << EOF
{
  "project_name": "test-project",
  "model": "test-model",
  "memory_store_type": "tinydb",
  "vector_store_enabled": true
}
EOF

echo "✅ Test environment setup complete!"
echo "📁 Test directory: $TEST_DIR"
echo "🔧 Environment variables configured for all optional services"
echo ""
echo "You can now run tests with:"
echo "  cd $TEST_DIR"
echo "  poetry run pytest tests/ -v"
echo ""
echo "Or run with coverage:"
echo "  cd $TEST_DIR"
echo "  poetry run coverage run --source=src/devsynth -m pytest tests/ --tb=no -q"

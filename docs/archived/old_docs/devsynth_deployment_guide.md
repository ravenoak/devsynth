
# DevSynth Deployment Guide

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
   - [3.1 Installation via pipx](#31-installation-via-pipx)
   - [3.2 Installation via pip](#32-installation-via-pip)
   - [3.3 Installation from Source](#33-installation-from-source)
4. [Configuration](#configuration)
   - [4.1 LM Studio Setup](#41-lm-studio-setup)
   - [4.2 DevSynth Configuration](#42-devsynth-configuration)
5. [Updating](#updating)
6. [Uninstallation](#uninstallation)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)
9. [References](#references)

## 1. Introduction

This guide provides detailed instructions for deploying, configuring, and operating DevSynth on a developer's local machine. DevSynth is a CLI application designed to help a single developer accelerate the software development lifecycle through AI-assisted automation.

DevSynth operates entirely on the developer's local machine, using LM Studio as the local LLM provider. This local-first approach ensures privacy, security, and minimal resource requirements.

## 2. System Requirements

DevSynth has the following system requirements:

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+ recommended)
- **Python**: Python 3.8 or higher
- **Disk Space**: 
  - DevSynth application: ~50MB
  - LM Studio: ~1GB (plus space for models)
  - Models: 4GB-10GB depending on model size
- **RAM**: 
  - DevSynth application: ~500MB
  - LM Studio: 8GB-16GB depending on model size
- **CPU**: Multi-core CPU (4+ cores recommended)
- **GPU**: Optional but recommended for faster LLM inference

## 3. Installation

DevSynth can be installed using pipx (recommended), pip, or from source.

### 3.1 Installation via pipx

[pipx](https://pypa.github.io/pipx/) is the recommended installation method as it creates an isolated environment for DevSynth and its dependencies.

1. Install pipx if not already installed:

```bash
# On macOS
brew install pipx
pipx ensurepath

# On Ubuntu/Debian
sudo apt update
sudo apt install python3-pip
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# On Windows
python -m pip install --user pipx
python -m pipx ensurepath
```

2. Install DevSynth using pipx:

```bash
pipx install devsynth
```

3. Verify the installation:

```bash
devsynth --version
```

### 3.2 Installation via pip

DevSynth can also be installed using pip:

```bash
pip install devsynth
```

Note that this will install DevSynth and its dependencies in your current Python environment. It's recommended to use a virtual environment if you choose this method:

```bash
python -m venv devsynth-env
source devsynth-env/bin/activate  # On Windows: devsynth-env\Scripts\activate
pip install devsynth
```

### 3.3 Installation from Source

To install DevSynth from source:

1. Clone the repository:

```bash
git clone https://github.com/username/dev-synth.git
cd dev-synth
```

2. Install the package in development mode:

```bash
pip install -e .
```

3. Verify the installation:

```bash
devsynth --version
```

## 4. Configuration

### 4.1 LM Studio Setup

DevSynth requires LM Studio to be installed and configured on your local machine:

1. Download and install LM Studio from [https://lmstudio.ai/](https://lmstudio.ai/)

2. Launch LM Studio and download a model:
   - Recommended models: Llama 3 8B, Mistral 7B, or CodeLlama 7B
   - Select a model appropriate for your hardware capabilities

3. Start the local server in LM Studio:
   - Click on "Local Server" in the sidebar
   - Select your downloaded model
   - Click "Start Server"
   - Note the server URL (typically http://localhost:1234)

### 4.2 DevSynth Configuration

DevSynth uses a configuration file to store settings. You can create or modify this file using the `config` command:

1. Initialize the configuration:

```bash
devsynth config init
```

2. Set the LM Studio endpoint:

```bash
devsynth config set llm.endpoint http://localhost:1234
```

3. Set the default model:

```bash
devsynth config set llm.model "Llama 3 8B"
```

4. Set token budget limits (optional):

```bash
devsynth config set tokens.default_budget 4000
```

5. View the current configuration:

```bash
devsynth config show
```

The configuration file is stored at `~/.devsynth/config.yaml` (or `%USERPROFILE%\.devsynth\config.yaml` on Windows).

## 5. Updating

To update DevSynth to the latest version:

### Using pipx

```bash
pipx upgrade devsynth
```

### Using pip

```bash
pip install --upgrade devsynth
```

### From source

```bash
cd dev-synth
git pull
pip install -e .
```

## 6. Uninstallation

To uninstall DevSynth:

### Using pipx

```bash
pipx uninstall devsynth
```

### Using pip

```bash
pip uninstall devsynth
```

To remove configuration files:

```bash
rm -rf ~/.devsynth  # On Windows: rmdir /s /q %USERPROFILE%\.devsynth
```

## 7. Troubleshooting

### Common Issues

#### LM Studio Connection Issues

If DevSynth cannot connect to LM Studio:

1. Ensure LM Studio is running and the server is started
2. Verify the endpoint URL in the DevSynth configuration
3. Check if the port is blocked by a firewall
4. Run the connection test:

```bash
devsynth config check-connection
```

#### High Memory Usage

If you experience high memory usage:

1. Use a smaller model in LM Studio
2. Reduce token budgets in DevSynth configuration:

```bash
devsynth config set tokens.default_budget 2000
```

3. Close other memory-intensive applications

#### Slow Performance

If DevSynth is running slowly:

1. Check your system resources (CPU, RAM, disk)
2. Use a smaller, faster model in LM Studio
3. Optimize token usage:

```bash
devsynth config set tokens.optimize true
```

### Logs

DevSynth logs are stored in:

- Linux/macOS: `~/.devsynth/logs/`
- Windows: `%USERPROFILE%\.devsynth\logs\`

To increase log verbosity:

```bash
devsynth --verbose [command]
```

## 8. Security Considerations

DevSynth is designed to operate entirely on your local machine, which provides inherent security benefits:

- No data is sent to external servers (except when explicitly configured)
- No API keys or credentials are required
- All processing occurs locally

However, there are still some security considerations:

- **Generated Code**: Always review generated code before execution
- **Project Data**: DevSynth has access to your project files, so be cautious when using it with sensitive projects
- **Model Security**: Ensure you download LM Studio models from trusted sources

## 9. References

- [DevSynth Documentation](https://github.com/username/dev-synth/docs)
- [LM Studio Documentation](https://lmstudio.ai/docs)
- [Python Package Installation Guide](https://packaging.python.org/en/latest/tutorials/installing-packages/)
- [pipx Documentation](https://pypa.github.io/pipx/)


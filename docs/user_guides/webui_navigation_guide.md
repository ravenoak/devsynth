# DevSynth WebUI Navigation Guide

## Introduction

The DevSynth Web User Interface (WebUI) provides a user-friendly way to interact with DevSynth's powerful features through your web browser. This guide will help you navigate the WebUI and understand the functionality available on each page.

## Getting Started

To launch the DevSynth WebUI, use the following command:

```bash
devsynth webui
```

This will start the Streamlit-based WebUI and open it in your default web browser. If it doesn't open automatically, you can access it at http://localhost:8501.

## Navigation Overview

The WebUI is organized into several pages, accessible through the sidebar on the left side of the screen. Each page corresponds to a specific DevSynth workflow or functionality.

### Sidebar Navigation

The sidebar contains links to all available pages:

- **Onboarding**: Initialize or configure a project
- **Requirements**: Gather and manage project requirements
- **Analysis**: Analyze code and project structure
- **Synthesis**: Generate code, tests, and documentation
- **Configuration**: Configure DevSynth settings
- **EDRR Cycle**: Run Expand-Differentiate-Refine-Reflect cycles
- **Alignment**: Align code with requirements
- **Diagnostics**: Run diagnostics and health checks

## Page Descriptions

### Onboarding Page

The Onboarding page allows you to initialize a new DevSynth project or configure an existing one.

**Features**:
- Initialize a new project with a specified path, language, and goals
- Run a guided setup wizard for more detailed configuration
- View initialization status and results

**Usage**:
1. Enter the project path (default is the current directory)
2. Specify the project root (if different from the path)
3. Select the primary programming language
4. Optionally, enter project goals
5. Click "Initialize" to create the project configuration

Alternatively, click "Guided Setup" for a step-by-step wizard that will help you configure your project in more detail.

### Requirements Page

The Requirements page helps you gather, inspect, and manage project requirements.

**Features**:
- Generate specifications from requirements
- Inspect existing requirements
- Edit specifications
- Interactive requirements wizard
- Requirements gathering wizard

**Usage**:
1. **Specification Generation**: Enter the path to your requirements file and click "Generate Specs" to create specifications
2. **Inspect Requirements**: Enter the path to a file and click "Inspect Requirements" to analyze its content
3. **Specification Editor**: Load, edit, and save specification files
4. **Requirements Wizard**: Create structured requirements with title, description, type, priority, and constraints
5. **Gather Wizard**: Run the requirements gathering wizard to collect project goals, constraints, and priorities

### Analysis Page

The Analysis page provides tools for analyzing your project's code and structure.

**Features**:
- Code inspection and analysis
- Project structure analysis
- Configuration inspection

**Usage**:
1. Enter the path to the file or directory you want to analyze
2. Select the type of analysis to perform
3. Click "Analyze" to start the analysis
4. View the analysis results and recommendations

### Synthesis Page

The Synthesis page allows you to generate code, tests, and documentation based on your project's specifications.

**Features**:
- Generate tests from specifications
- Generate code from tests
- Run the complete synthesis pipeline
- View generation results

**Usage**:
1. **Test Generation**: Enter the path to your specification file and output directory, then click "Generate Tests"
2. **Code Generation**: Enter the output directory and click "Generate Code"
3. **Run Pipeline**: Select a target component and click "Run Pipeline" to execute the complete synthesis workflow

### Configuration Page

The Configuration page allows you to view and modify DevSynth's configuration settings.

**Features**:
- View current configuration
- Update configuration settings
- Reset to default configuration

**Usage**:
1. Browse the current configuration settings
2. Modify settings as needed
3. Click "Save" to apply changes
4. Click "Reset" to restore default settings

### EDRR Cycle Page

The EDRR Cycle page allows you to run Expand-Differentiate-Refine-Reflect cycles for iterative improvement of your project.

**Features**:
- Run EDRR cycles with custom prompts
- Provide additional context for the cycle
- Set the maximum number of iterations
- View cycle results and recommendations

**Usage**:
1. Enter a prompt describing what you want to improve or develop
2. Optionally, provide additional context
3. Set the maximum number of iterations
4. Click "Run EDRR Cycle" to start the process
5. View the results and follow the recommendations

### Alignment Page

The Alignment page helps you ensure that your code aligns with your project's requirements and specifications.

**Features**:
- Check alignment between code and requirements
- Generate alignment metrics
- View alignment reports

**Usage**:
1. Enter the paths to your code, requirements, and specifications
2. Click "Check Alignment" to analyze the alignment
3. View the alignment report and metrics
4. Follow recommendations to improve alignment

### Diagnostics Page

The Diagnostics page provides tools for checking the health of your project and DevSynth installation.

**Features**:
- Run the doctor command to check for issues
- Validate project manifest and metadata
- Run test metrics
- Generate documentation

**Usage**:
1. **Doctor**: Enter the project path and click "Run Doctor" to check for issues
2. **Validate Manifest**: Click "Validate Manifest" to check your project's manifest file
3. **Validate Metadata**: Click "Validate Metadata" to check your project's metadata
4. **Test Metrics**: Click "Run Test Metrics" to analyze your project's test coverage and quality
5. **Generate Docs**: Click "Generate Docs" to create documentation for your project

## Tips for Effective Use

- **Use the Sidebar**: The sidebar is always available for navigation between pages
- **Progress Indicators**: Look for progress bars and spinners to track long-running operations
- **Error Messages**: Pay attention to error messages (in red) for troubleshooting
- **Success Messages**: Green messages indicate successful operations
- **Help Text**: Most inputs have help text explaining their purpose
- **Consistent Workflow**: Follow the natural workflow from requirements to analysis to synthesis

## Troubleshooting

If you encounter issues with the WebUI:

1. **Check Console Output**: Look at the terminal where you launched the WebUI for error messages
2. **Refresh the Page**: Sometimes a simple refresh can resolve UI issues
3. **Restart the WebUI**: Stop the WebUI (Ctrl+C in the terminal) and restart it
4. **Check Logs**: Examine the DevSynth logs for more detailed error information
5. **Run Doctor**: Use the Diagnostics page to run the doctor command, which can identify and fix common issues

## Conclusion

The DevSynth WebUI provides a user-friendly interface to DevSynth's powerful features. By understanding the purpose and functionality of each page, you can effectively use DevSynth to streamline your development workflow.

For more detailed information about specific features, refer to the DevSynth documentation or use the CLI help command:

```bash
devsynth help
```
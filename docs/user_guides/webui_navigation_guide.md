---

title: "DevSynth WebUI Navigation Guide"
date: "2025-07-07"
version: "0.1.0a1"
tags:
  - "user-guide"
  - "guide"

status: "published"
author: "DevSynth Team"
last_reviewed: "2025-07-10"
---
<div class="breadcrumbs">
<a href="../index.md">Documentation</a> &gt; <a href="index.md">User Guides</a> &gt; DevSynth WebUI Navigation Guide
</div>

# DevSynth WebUI Navigation Guide

## Introduction

The DevSynth Web User Interface (WebUI) is built with NiceGUI and provides a user-friendly way to interact with DevSynth's powerful features through your web browser. This guide will help you navigate the WebUI and understand the functionality available on each page.

![DevSynth WebUI Overview](../images/webui/webui_overview.png)

## Getting Started

To launch the DevSynth WebUI, use the following command:

```bash
devsynth webui
```

This will start the NiceGUI-based WebUI and open it in your default web browser. If it doesn't open automatically, you can access it at http://localhost:8080.

![WebUI Launch Screen](../images/webui/webui_launch.png)

## Navigation Overview

The WebUI is organized into several pages, accessible through the sidebar on the left side of the screen. Each page corresponds to a specific DevSynth workflow or functionality.

### Sidebar Navigation

The sidebar contains links to all available pages:

- **Onboarding**: Initialize or configure a project
- **Requirements**: Gather and manage project requirements
- **Analysis**: Analyze code and project structure
- **Synthesis**: Generate code, tests, and documentation
- **Configuration**: Configure DevSynth settings
- **EDRR**: Run Expand-Differentiate-Refine-Reflect cycles
- **Alignment**: Align code with requirements
- **Diagnostics**: Run diagnostics and health checks


![Sidebar Navigation](../images/webui/sidebar_navigation.png)

## Page Descriptions

### Onboarding Page

The Onboarding page allows you to initialize a new DevSynth project or configure an existing one.

![Onboarding Page](../images/webui/onboarding_page.png)

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

### Onboarding Page Element

The Onboarding page contains the following UI elements:

- **Project Path Input**: Text field for entering the project path
- **Project Root Input**: Text field for specifying the project root
- **Language Selector**: Dropdown menu for selecting the primary programming language
- **Goals Input**: Text area for entering project goals
- **Initialize Button**: Button to start the initialization process
- **Guided Setup Button**: Button to launch the guided setup wizard
- **Status Area**: Section displaying initialization status and results


Navigation: From the Onboarding page, you can navigate to the Requirements page after initializing a project.

## Workflow: Project Initialization

Here's a complete workflow for initializing a new project:

1. Navigate to the Onboarding page from the sidebar
2. Enter the project path (e.g., "./my-new-project")
3. Select the primary programming language (e.g., "Python")
4. Enter project goals (e.g., "A CLI tool for managing tasks")
5. Click "Initialize"
6. Wait for the initialization to complete
7. Review the initialization status and results
8. Navigate to the Requirements page to start defining requirements


![Project Initialization Workflow](../images/webui/project_init_workflow.png)

### Requirements Page

The Requirements page helps you gather, inspect, and manage project requirements.

![Requirements Page](../images/webui/requirements_page.png)

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


### Requirements Page Element

The Requirements page contains the following UI elements:

- **Requirements File Input**: Text field for entering the path to the requirements file
- **Generate Specs Button**: Button to generate specifications from requirements
- **Inspect Requirements Button**: Button to analyze requirements
- **Specification Editor**: Text area for editing specifications
- **Requirements Wizard**: Form for creating structured requirements
- **Gather Wizard Button**: Button to launch the requirements gathering wizard
- **Results Area**: Section displaying generation and inspection results


Navigation: From the Requirements page, you can navigate to the Analysis page after generating specifications.

## Workflow: Requirements to Specifications

Here's a complete workflow for generating specifications from requirements:

1. Navigate to the Requirements page from the sidebar
2. Enter the path to your requirements file (e.g., "requirements.md")
3. Click "Generate Specs"
4. Wait for the generation to complete
5. Review the generated specifications
6. Optionally, edit the specifications in the editor
7. Save the specifications
8. Navigate to the Analysis page to analyze the specifications


![Requirements to Specifications Workflow](../images/webui/requirements_to_specs_workflow.png)

### Analysis Page

The Analysis page provides tools for analyzing your project's code and structure.

![Analysis Page](../images/webui/analysis_page.png)

**Features**:

- Code inspection and analysis
- Project structure analysis
- Configuration inspection


**Usage**:

1. Enter the path to the file or directory you want to analyze
2. Select the type of analysis to perform
3. Click "Analyze" to start the analysis
4. View the analysis results and recommendations


### Analysis Page Element

The Analysis page contains the following UI elements:

- **Path Input**: Text field for entering the path to the file or directory
- **Analysis Type Selector**: Dropdown menu for selecting the type of analysis
- **Analyze Button**: Button to start the analysis
- **Results Area**: Section displaying analysis results and recommendations


Navigation: From the Analysis page, you can navigate to the Synthesis page after analyzing your project.

## Workflow: Code Analysis

Here's a complete workflow for analyzing code:

1. Navigate to the Analysis page from the sidebar
2. Enter the path to your code (e.g., "src/main.py")
3. Select the analysis type (e.g., "Code Quality")
4. Click "Analyze"
5. Wait for the analysis to complete
6. Review the analysis results and recommendations
7. Navigate to the Synthesis page to generate tests or code


![Code Analysis Workflow](../images/webui/code_analysis_workflow.png)

### Synthesis Page

The Synthesis page allows you to generate code, tests, and documentation based on your project's specifications.

![Synthesis Page](../images/webui/synthesis_page.png)

**Features**:

- Generate tests from specifications
- Generate code from tests
- Run the complete synthesis pipeline
- View generation results


**Usage**:

1. **Test Generation**: Enter the path to your specification file and output directory, then click "Generate Tests"
2. **Code Generation**: Enter the output directory and click "Generate Code"
3. **Run Pipeline**: Select a target component and click "Run Pipeline" to execute the complete synthesis workflow


### Synthesis Page Element

The Synthesis page contains the following UI elements:

- **Specification File Input**: Text field for entering the path to the specification file
- **Output Directory Input**: Text field for entering the output directory
- **Generate Tests Button**: Button to generate tests from specifications
- **Generate Code Button**: Button to generate code from tests
- **Target Selector**: Dropdown menu for selecting the target component
- **Run Pipeline Button**: Button to execute the complete synthesis workflow
- **Results Area**: Section displaying generation results


Navigation: From the Synthesis page, you can navigate to the Configuration page to configure DevSynth settings.

## Workflow: Generating Tests and Code

Here's a complete workflow for generating tests and code:

1. Navigate to the Synthesis page from the sidebar
2. Enter the path to your specification file (e.g., "specs.md")
3. Enter the output directory for tests (e.g., "tests")
4. Click "Generate Tests"
5. Wait for the test generation to complete
6. Enter the output directory for code (e.g., "src")
7. Click "Generate Code"
8. Wait for the code generation to complete
9. Review the generation results
10. Navigate to the Configuration page to configure DevSynth settings


![Generating Tests and Code Workflow](../images/webui/generating_tests_code_workflow.png)

### Configuration Page

The Configuration page allows you to view and modify DevSynth's configuration settings.

![Configuration Page](../images/webui/configuration_page.png)

**Features**:

- View current configuration
- Update configuration settings
- Reset to default configuration


**Usage**:

1. Browse the current configuration settings
2. Modify settings as needed
3. Click "Save" to apply changes
4. Click "Reset" to restore default settings


### Configuration Page Element

The Configuration page contains the following UI elements:

- **Configuration Settings**: Form for viewing and modifying configuration settings
- **Save Button**: Button to apply configuration changes
- **Reset Button**: Button to restore default configuration
- **Status Area**: Section displaying configuration status and results


Navigation: From the Configuration page, you can navigate to the EDRR page to run EDRR cycles.

## Workflow: Configuring DevSynth

Here's a complete workflow for configuring DevSynth:

1. Navigate to the Configuration page from the sidebar
2. Browse the current configuration settings
3. Modify settings as needed (e.g., change the LLM model)
4. Click "Save"
5. Wait for the configuration to be saved
6. Review the configuration status and results
7. Navigate to the EDRR page to run EDRR cycles


![Configuring DevSynth Workflow](../images/webui/configuring_devsynth_workflow.png)

### EDRR Page

The EDRR page allows you to run Expand-Differentiate-Refine-Reflect cycles for iterative improvement of your project.

![EDRR Page](../images/webui/edrr_cycle_page.png)

**Features**:

- Run EDRR cycles with custom prompts
- Provide additional context for the cycle
- Set the maximum number of iterations
- View cycle results and recommendations


**Usage**:

1. Enter a prompt describing what you want to improve or develop
2. Optionally, provide additional context
3. Set the maximum number of iterations
4. Click "Run EDRR" to start the process
5. View the results and follow the recommendations


### EDRR Page Element

The EDRR page contains the following UI elements:

- **Prompt Input**: Text area for entering the EDRR prompt
- **Context Input**: Text area for providing additional context
- **Iterations Input**: Number input for setting the maximum number of iterations
- **Run EDRR Button**: Button to start the EDRR
- **Results Area**: Section displaying cycle results and recommendations


Navigation: From the EDRR page, you can navigate to the Alignment page to check alignment.

## Workflow: Running an EDRR

Here's a complete workflow for running an EDRR:

1. Navigate to the EDRR page from the sidebar
2. Enter a prompt (e.g., "Improve error handling in the API endpoints")
3. Provide additional context if needed
4. Set the maximum number of iterations (e.g., 3)
5. Click "Run EDRR"
6. Wait for the cycle to complete
7. Review the results and recommendations
8. Navigate to the Alignment page to check alignment


![Running an EDRR Workflow](../images/webui/running_edrr_cycle_workflow.png)

### Alignment Page

The Alignment page helps you ensure that your code aligns with your project's requirements and specifications.

![Alignment Page](../images/webui/alignment_page.png)

**Features**:

- Check alignment between code and requirements
- Generate alignment metrics
- View alignment reports


**Usage**:

1. Enter the paths to your code, requirements, and specifications
2. Click "Check Alignment" to analyze the alignment
3. View the alignment report and metrics
4. Follow recommendations to improve alignment


### Alignment Page Element

The Alignment page contains the following UI elements:

- **Code Directory Input**: Text field for entering the path to the code directory
- **Requirements File Input**: Text field for entering the path to the requirements file
- **Specifications File Input**: Text field for entering the path to the specifications file
- **Check Alignment Button**: Button to analyze alignment
- **Results Area**: Section displaying alignment report and metrics


Navigation: From the Alignment page, you can navigate to the Diagnostics page to check project health.

## Workflow: Checking Alignment

Here's a complete workflow for checking alignment:

1. Navigate to the Alignment page from the sidebar
2. Enter the path to your code directory (e.g., "src")
3. Enter the path to your requirements file (e.g., "requirements.md")
4. Enter the path to your specifications file (e.g., "specs.md")
5. Click "Check Alignment"
6. Wait for the alignment check to complete
7. Review the alignment report and metrics
8. Follow recommendations to improve alignment
9. Navigate to the Diagnostics page to check project health


![Checking Alignment Workflow](../images/webui/checking_alignment_workflow.png)

### Diagnostics Page

The Diagnostics page provides tools for checking the health of your project and DevSynth installation.

![Diagnostics Page](../images/webui/diagnostics_page.png)

**Features**:

- Run the doctor command to check for issues
- Validate `.devsynth/project.yaml` and metadata
- Run test metrics
- Generate documentation


**Usage**:

1. **Doctor**: Enter the project path and click "Run Doctor" to check for issues
2. **Validate Manifest**: Click "Validate Manifest" to check your project's manifest file
3. **Validate Metadata**: Click "Validate Metadata" to check your project's metadata
4. **Test Metrics**: Click "Run Test Metrics" to analyze your project's test coverage and quality
5. **Generate Docs**: Click "Generate Docs" to create documentation for your project


### Diagnostics Page Element

The Diagnostics page contains the following UI elements:

- **Project Path Input**: Text field for entering the project path
- **Run Doctor Button**: Button to check for issues
- **Validate Manifest Button**: Button to check the manifest file
- **Validate Metadata Button**: Button to check the metadata
- **Run Test Metrics Button**: Button to analyze test coverage and quality
- **Generate Docs Button**: Button to create documentation
- **Results Area**: Section displaying diagnostic results


Navigation: From the Diagnostics page, you can navigate to any other page using the sidebar.

## Workflow: Running Diagnostics

Here's a complete workflow for running diagnostics:

1. Navigate to the Diagnostics page from the sidebar
2. Enter the project path (e.g., "./my-project")
3. Click "Run Doctor"
4. Wait for the doctor check to complete
5. Review the diagnostic results
6. Click "Validate Manifest"
7. Wait for the validation to complete
8. Review the validation results
9. Click "Run Test Metrics"
10. Wait for the metrics to be generated
11. Review the test metrics
12. Click "Generate Docs"
13. Wait for the documentation to be generated
14. Review the documentation generation results


![Running Diagnostics Workflow](../images/webui/running_diagnostics_workflow.png)

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

## Implementation Status

This feature is **implemented** and available for use. The WebUI can be launched using the `devsynth webui` command as described in this guide.

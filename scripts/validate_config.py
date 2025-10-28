#!/usr/bin/env python3
"""
Configuration Validation Script

This script validates DevSynth configuration files to ensure they are well-formed
and contain all required fields with appropriate types.
"""

import argparse
import os
import sys
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

# Configuration schema definition
CONFIG_SCHEMA = {
    "type": "object",
    "required": [
        "application",
        "logging",
        "memory",
        "llm",
        "agents",
        "edrr",
        "security",
        "performance",
        "features",
    ],
    "properties": {
        "application": {
            "type": "object",
            "required": ["name", "version"],
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
                "description": {"type": "string"},
            },
        },
        "logging": {
            "type": "object",
            "required": ["level", "format"],
            "properties": {
                "level": {
                    "type": "string",
                    "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                },
                "format": {"type": "string"},
                "file": {"type": ["string", "null"]},
            },
        },
        "memory": {
            "type": "object",
            "required": ["default_store", "stores"],
            "properties": {
                "default_store": {"type": "string"},
                "stores": {
                    "type": "object",
                    "required": ["chromadb", "kuzu"],
                    "properties": {
                        "chromadb": {
                            "type": "object",
                            "required": ["enabled"],
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "collection_name": {"type": "string"},
                                "distance_function": {"type": "string"},
                                "persist_directory": {"type": "string"},
                                "host": {"type": ["string", "null"]},
                                "port": {"type": "integer"},
                            },
                        },
                        "kuzu": {
                            "type": "object",
                            "properties": {"persist_directory": {"type": "string"}},
                        },
                        "faiss": {
                            "type": "object",
                            "required": ["enabled"],
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "index_file": {"type": "string"},
                                "dimension": {"type": "integer"},
                            },
                        },
                    },
                },
            },
        },
        "llm": {
            "type": "object",
            "required": ["default_provider", "providers"],
            "properties": {
                "default_provider": {"type": "string"},
                "providers": {
                    "type": "object",
                    "properties": {
                        "openai": {
                            "type": "object",
                            "required": ["enabled"],
                            "properties": {
                                "enabled": {"type": "boolean"},
                                "model": {"type": "string"},
                                "temperature": {
                                    "type": "number",
                                    "minimum": 0,
                                    "maximum": 1,
                                },
                                "max_tokens": {"type": "integer", "minimum": 1},
                                "timeout": {"type": "integer", "minimum": 1},
                            },
                        }
                    },
                },
            },
        },
        "agents": {
            "type": "object",
            "required": ["max_agents", "default_timeout"],
            "properties": {
                "max_agents": {"type": "integer", "minimum": 1},
                "default_timeout": {"type": "integer", "minimum": 1},
                "memory_context_size": {"type": "integer", "minimum": 1},
            },
        },
        "edrr": {
            "type": "object",
            "required": ["enabled"],
            "properties": {
                "enabled": {"type": "boolean"},
                "default_phase": {"type": "string"},
                "phase_transition": {
                    "type": "object",
                    "properties": {
                        "auto": {"type": "boolean"},
                        "timeout": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
        "security": {
            "type": "object",
            "required": ["input_validation"],
            "properties": {
                "input_validation": {"type": "boolean"},
                "rate_limiting": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "max_requests": {"type": "integer", "minimum": 1},
                        "period": {"type": "integer", "minimum": 1},
                    },
                },
                "encryption": {
                    "type": "object",
                    "properties": {
                        "at_rest": {"type": "boolean"},
                        "in_transit": {"type": "boolean"},
                    },
                },
            },
        },
        "performance": {
            "type": "object",
            "properties": {
                "cache": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "ttl": {"type": "integer", "minimum": 1},
                    },
                },
                "concurrency": {
                    "type": "object",
                    "properties": {
                        "max_workers": {"type": ["integer", "string"], "minimum": 1},
                        "timeout": {"type": "integer", "minimum": 1},
                    },
                },
            },
        },
        "features": {
            "type": "object",
            "properties": {
                "wsde_collaboration": {"type": "boolean"},
                "dialectical_reasoning": {"type": "boolean"},
                "code_generation": {"type": "boolean"},
                "test_generation": {"type": "boolean"},
                "documentation_generation": {"type": "boolean"},
                "experimental_features": {"type": "boolean"},
                "prompt_auto_tuning": {"type": "boolean"},
                "automatic_phase_transitions": {"type": "boolean"},
                "collaboration_notifications": {"type": "boolean"},
                "edrr_framework": {"type": "boolean"},
                "micro_edrr_cycles": {"type": "boolean"},
                "recursive_edrr": {"type": "boolean"},
                "wsde_peer_review": {"type": "boolean"},
                "wsde_consensus_voting": {"type": "boolean"},
                "uxbridge_webui": {"type": "boolean"},
                "uxbridge_agent_api": {"type": "boolean"},
                "gui": {"type": "boolean"},
                "mvuu_dashboard": {"type": "boolean"},
            },
        },
    },
}


def load_config(file_path: str) -> dict[str, Any]:
    """Load a YAML configuration file."""
    try:
        with open(file_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading configuration file {file_path}: {e}")
        sys.exit(1)


def validate_config(config: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate a configuration against a schema."""
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    return [
        f"{'.'.join(str(p) for p in error.path)}: {error.message}" for error in errors
    ]


def validate_environment_variables(config: dict[str, Any]) -> list[str]:
    """Check for environment variables in the configuration and validate they're set."""
    errors = []

    def check_env_vars(obj, path=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                new_path = f"{path}.{key}" if path else key
                check_env_vars(value, new_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_env_vars(item, f"{path}[{i}]")
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            # Extract the environment variable name
            env_var = obj[2:-1]
            if ":-" in env_var:  # Has default value
                env_var = env_var.split(":-")[0]

            if not os.environ.get(env_var):
                errors.append(
                    f"Environment variable {env_var} referenced in {path} is not set"
                )

    check_env_vars(config)
    return errors


def check_config_consistency(configs: dict[str, dict[str, Any]]) -> list[str]:
    """Check consistency across different environment configurations."""
    errors = []

    # Check that all environments have the same feature flags
    default_features = set(configs.get("default", {}).get("features", {}).keys())
    for env, config in configs.items():
        if env == "default":
            continue

        env_features = set(config.get("features", {}).keys())
        missing_features = default_features - env_features
        if missing_features:
            errors.append(
                f"Environment {env} is missing feature flags: {', '.join(missing_features)}"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate DevSynth configuration files"
    )
    parser.add_argument(
        "--config-dir",
        default="./config",
        help="Directory containing configuration files",
    )
    parser.add_argument(
        "--environments",
        nargs="+",
        default=["default", "development", "testing", "staging", "production"],
        help="Environments to validate",
    )
    args = parser.parse_args()

    configs = {}
    all_errors = []

    # Load and validate each configuration file
    for env in args.environments:
        config_path = os.path.join(args.config_dir, f"{env}.yml")
        if not os.path.exists(config_path):
            print(
                f"Warning: Configuration file for environment {env} not found at {config_path}"
            )
            continue

        print(f"Validating {env} configuration...")
        config = load_config(config_path)
        configs[env] = config

        # Validate against schema
        schema_errors = validate_config(config, CONFIG_SCHEMA)
        if schema_errors:
            all_errors.extend([f"[{env}] {error}" for error in schema_errors])

        # Validate environment variables
        env_var_errors = validate_environment_variables(config)
        if env_var_errors:
            all_errors.extend([f"[{env}] {error}" for error in env_var_errors])

    # Check consistency across configurations
    consistency_errors = check_config_consistency(configs)
    if consistency_errors:
        all_errors.extend([f"[consistency] {error}" for error in consistency_errors])

    # Report results
    if all_errors:
        print("\nValidation errors found:")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("\nAll configurations are valid!")
        sys.exit(0)


if __name__ == "__main__":
    main()

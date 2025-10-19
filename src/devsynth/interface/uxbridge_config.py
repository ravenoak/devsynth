"""Configuration utilities for UXBridge implementations.

This module provides utilities for ensuring consistent behavior across
all UXBridge implementations based on configuration settings.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Type, cast

from devsynth.config import ProjectUnifiedConfig
from devsynth.interface.ux_bridge import UXBridge
from devsynth.logging_setup import DevSynthLogger

# Module level logger
logger = DevSynthLogger(__name__)


def apply_uxbridge_settings(
    bridge_class: Type[UXBridge], config: ProjectUnifiedConfig, **kwargs: Any
) -> UXBridge:
    """Apply uxbridge_settings from configuration to a UXBridge implementation.

    Args:
        bridge_class: The UXBridge implementation class to instantiate
        config: The project configuration
        **kwargs: Additional keyword arguments to pass to the bridge constructor

    Returns:
        An instance of the UXBridge implementation with settings applied
    """
    # Get UXBridge settings from configuration
    uxbridge_settings = config.config.uxbridge_settings or {}

    # Create an instance of the bridge class with appropriate settings
    bridge_instance = bridge_class(**kwargs)

    # Log the settings being applied
    logger.debug(
        f"Applying UXBridge settings to {bridge_class.__name__}: {uxbridge_settings}"
    )

    # Apply any additional settings based on the bridge class
    # This can be extended as needed for specific bridge implementations

    return bridge_instance


def get_default_bridge(config: Optional[ProjectUnifiedConfig] = None) -> UXBridge:
    """Get the default UXBridge implementation based on configuration.

    Args:
        config: The project configuration, or None to load the default

    Returns:
        An instance of the default UXBridge implementation
    """
    from devsynth.config import load_project_config
    from devsynth.interface.cli import CLIUXBridge

    # Load configuration if not provided
    if config is None:
        config = load_project_config()

    # Get UXBridge settings from configuration
    uxbridge_settings = config.config.uxbridge_settings or {}
    default_interface = uxbridge_settings.get("default_interface", "cli")

    # Determine which bridge to use based on configuration
    if default_interface == "webui" and config.config.features.get(
        "uxbridge_webui", False
    ):
        try:
            import importlib.util
            import sys
            from pathlib import Path

            # Load the webui.py module directly
            webui_path = Path(__file__).parent / "webui.py"
            spec = importlib.util.spec_from_file_location(
                "devsynth.interface.webui_module", webui_path
            )
            if spec and spec.loader:
                webui_module = importlib.util.module_from_spec(spec)
                sys.modules["devsynth.interface.webui_module"] = webui_module
                spec.loader.exec_module(webui_module)
                WebUI = webui_module.WebUI
            else:
                raise ImportError("Could not load webui module")

            logger.debug("Using WebUI as default UXBridge implementation")
            return apply_uxbridge_settings(cast(Type[UXBridge], WebUI), config)
        except ImportError:
            logger.warning(
                "WebUI requested but Streamlit not available, falling back to CLI"
            )
            return apply_uxbridge_settings(CLIUXBridge, config)
    elif default_interface == "api" and config.config.features.get(
        "uxbridge_agent_api", False
    ):
        try:
            from devsynth.interface.agentapi import APIBridge

            logger.debug("Using APIBridge as default UXBridge implementation")
            return apply_uxbridge_settings(APIBridge, config)
        except ImportError:
            logger.warning(
                "API requested but FastAPI not available, falling back to CLI"
            )
            return apply_uxbridge_settings(CLIUXBridge, config)
    else:
        # Default to CLI
        logger.debug("Using CLIUXBridge as default UXBridge implementation")
        return apply_uxbridge_settings(CLIUXBridge, config)


__all__ = ["apply_uxbridge_settings", "get_default_bridge"]

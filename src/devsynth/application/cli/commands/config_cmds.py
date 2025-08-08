"""Configuration management commands."""

from ..registry import register
from .config_cmd import config_app, config_cmd, enable_feature_cmd

register("config", config_cmd)
register("enable-feature", enable_feature_cmd)

__all__ = ["config_app", "config_cmd", "enable_feature_cmd"]
